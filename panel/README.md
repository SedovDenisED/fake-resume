# Панель клиентов Happ (FastAPI)

Работает на домашнем MiniPC, слушает адрес в AWG-сети (по умолчанию `10.66.66.1:8080`).
С лендинга: 5 кликов по логотипу SDE → этот URL.

## Запуск

```bash
cd panel
cp .env.example .env
# задать PANEL_SECRET, PANEL_PASSWORD, VLESS_PATH, LISTEN_HOST=10.66.66.1
uv sync
uv run uvicorn panel.main:app --host 10.66.66.1 --port 8080
```

Локально для отладки: `LISTEN_HOST=127.0.0.1`, `RP_ID=localhost`, `ORIGIN=http://127.0.0.1:8080`.

## systemd (пример)

```ini
[Unit]
Description=Fake Resume Panel
After=network-online.target

[Service]
WorkingDirectory=/opt/fake-resume/panel
EnvironmentFile=/opt/fake-resume/panel/.env
ExecStart=/opt/fake-resume/panel/.venv/bin/uvicorn panel.main:app --host ${LISTEN_HOST} --port ${LISTEN_PORT}
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## После создания клиентов

Файл `data/singbox-users.json` — вставь `users` в конфиг sing-box и перезапусти.
Либо задай `RELOAD_HOOK` в `.env`.
