"""Сборка VLESS-ссылок и экспорт пользователей."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from urllib.parse import quote

from panel.config import settings
from panel.models import Client

logger = logging.getLogger("panel.vless")


def build_share_link(client: Client) -> str:
    """VLESS URI для Happ."""
    path = settings.vless_path if settings.vless_path.startswith("/") else f"/{settings.vless_path}"
    query = (
        f"encryption=none&security=tls&sni={quote(settings.vless_sni)}"
        f"&type=xhttp&path={quote(path)}&host={quote(settings.vless_sni)}"
    )
    name = quote(client.name or client.remark or "client")
    return f"vless://{client.uuid}@{settings.vless_host}:{settings.vless_port}?{query}#{name}"


def export_singbox_users(clients: list[Client]) -> None:
    """Пишет фрагмент users для sing-box."""
    path = Path(settings.singbox_export_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "users": [{"name": c.name, "uuid": c.uuid} for c in clients],
        "path": settings.vless_path,
        "note": "Вставь users в inbounds[0].users конфига sing-box и перезапусти сервис",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("exported %s users to %s", len(clients), path)
    if settings.reload_hook:
        try:
            subprocess.run(settings.reload_hook, shell=True, check=False, timeout=30)
        except OSError as exc:
            logger.error("reload_hook failed: %s", exc)
