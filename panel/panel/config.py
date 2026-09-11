"""Настройки панели управления."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Параметры окружения панели."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    panel_secret: str = "change-me-long-random-secret"
    panel_password: str = "change-me"
    database_url: str = f"sqlite:///{Path(__file__).resolve().parent.parent / 'data' / 'panel.db'}"
    session_cookie: str = "fr_panel_session"
    session_max_age: int = 60 * 60 * 24 * 7
    listen_host: str = "10.66.66.1"
    listen_port: int = 8080
    vless_host: str = "resume.sde-lab.ru"
    vless_port: int = 443
    vless_path: str = "/REPLACE_SECRET_PATH"
    vless_sni: str = "resume.sde-lab.ru"
    rp_id: str = "10.66.66.1"
    rp_name: str = "Fake Resume Panel"
    origin: str = "http://10.66.66.1:8080"
    singbox_export_path: str = str(Path(__file__).resolve().parent.parent / "data" / "singbox-users.json")
    reload_hook: str = ""


settings = Settings()
