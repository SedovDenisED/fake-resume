"""Приложение панели управления клиентами Happ."""

from __future__ import annotations

import io
import logging
import uuid
from pathlib import Path
from typing import Annotated

import qrcode
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from panel.auth import (
    create_session_token,
    finish_webauthn_authentication,
    finish_webauthn_registration,
    is_authenticated,
    require_auth,
    start_webauthn_authentication,
    start_webauthn_registration,
    verify_password,
)
from panel.config import settings
from panel.db import get_db, init_db
from panel.models import Client
from panel.vless import build_share_link, export_singbox_users

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("panel")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Fake Resume Panel", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.middleware("http")
async def access_log(request: Request, call_next):
    """Пишет access-лог запросов."""
    response = await call_next(request)
    logger.info(
        "%s %s %s",
        request.client.host if request.client else "-",
        request.method,
        request.url.path,
    )
    return response


@app.on_event("startup")
def on_startup() -> None:
    """Инициализация БД при старте."""
    init_db()
    logger.info("panel ready host=%s port=%s", settings.listen_host, settings.listen_port)


def _clients_export(db: Session) -> None:
    export_singbox_users(db.query(Client).order_by(Client.id).all())


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    """Страница входа."""
    if is_authenticated(request):
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"error": None},
    )


@app.post("/login")
def login_submit(
    request: Request,
    password: Annotated[str, Form()],
) -> Response:
    """Вход по паролю."""
    if not verify_password(password):
        logger.warning("failed login from %s", request.client.host if request.client else "-")
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверный пароль"},
            status_code=401,
        )
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        settings.session_cookie,
        create_session_token(),
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age,
    )
    logger.info("password login ok")
    return response


@app.post("/logout")
def logout(_: Annotated[None, Depends(require_auth)]) -> Response:
    """Выход."""
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(settings.session_cookie)
    return response


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Список клиентов."""
    if not is_authenticated(request):
        return RedirectResponse("/login", status_code=303)
    clients = db.query(Client).order_by(Client.id).all()
    rows = [{"client": c, "link": build_share_link(c)} for c in clients]
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "rows": rows,
            "vless_host": settings.vless_host,
            "vless_path": settings.vless_path,
            "max_clients": 4,
        },
    )


@app.post("/clients")
def create_client(
    _: Annotated[None, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
    name: Annotated[str, Form()],
    remark: Annotated[str, Form()] = "",
) -> Response:
    """Создаёт клиента."""
    name = name.strip()
    if not name:
        raise HTTPException(400, "name required")
    count = db.query(Client).count()
    if count >= 4:
        raise HTTPException(400, "max 4 clients")
    if db.query(Client).filter(Client.name == name).first():
        raise HTTPException(400, "name exists")
    client = Client(name=name, remark=remark.strip(), uuid=str(uuid.uuid4()))
    db.add(client)
    db.commit()
    _clients_export(db)
    logger.info("created client %s uuid=%s", client.name, client.uuid)
    return RedirectResponse("/", status_code=303)


@app.post("/clients/{client_id}/rotate")
def rotate_client(
    client_id: int,
    _: Annotated[None, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Ротация UUID клиента."""
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404)
    client.uuid = str(uuid.uuid4())
    db.commit()
    _clients_export(db)
    logger.info("rotated client %s", client.name)
    return RedirectResponse("/", status_code=303)


@app.post("/clients/{client_id}/delete")
def delete_client(
    client_id: int,
    _: Annotated[None, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Удаляет клиента."""
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404)
    name = client.name
    db.delete(client)
    db.commit()
    _clients_export(db)
    logger.info("deleted client %s", name)
    return RedirectResponse("/", status_code=303)


@app.get("/clients/{client_id}/qr")
def client_qr(
    client_id: int,
    _: Annotated[None, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """QR-код share-ссылки."""
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(404)
    link = build_share_link(client)
    img = qrcode.make(link)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


@app.get("/api/webauthn/register/options")
def webauthn_reg_options(_: Annotated[None, Depends(require_auth)]) -> Response:
    """Опции регистрации Face ID / passkey."""
    return Response(content=start_webauthn_registration(), media_type="application/json")


@app.post("/api/webauthn/register/verify")
async def webauthn_reg_verify(
    request: Request,
    _: Annotated[None, Depends(require_auth)],
    db: Annotated[Session, Depends(get_db)],
) -> dict[str, bool]:
    """Завершение регистрации passkey."""
    body = await request.json()
    finish_webauthn_registration(body, db)
    return {"ok": True}


@app.get("/api/webauthn/login/options")
def webauthn_login_options(db: Annotated[Session, Depends(get_db)]) -> Response:
    """Опции входа passkey."""
    return Response(content=start_webauthn_authentication(db), media_type="application/json")


@app.post("/api/webauthn/login/verify")
async def webauthn_login_verify(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Вход по passkey."""
    body = await request.json()
    finish_webauthn_authentication(body, db)
    response = Response(content='{"ok":true}', media_type="application/json")
    response.set_cookie(
        settings.session_cookie,
        create_session_token(),
        httponly=True,
        samesite="lax",
        max_age=settings.session_max_age,
    )
    logger.info("webauthn login ok")
    return response


def run() -> None:
    """Точка входа uvicorn."""
    import uvicorn

    uvicorn.run(
        "panel.main:app",
        host=settings.listen_host,
        port=settings.listen_port,
        reload=False,
    )


if __name__ == "__main__":
    run()
