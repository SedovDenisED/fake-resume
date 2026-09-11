# sing-box VLESS + WebSocket на доме

Официальный sing-box **не поддерживает xhttp** (это Xray / форки). Используем `ws` — нормально работает с Caddy reverse_proxy и Happ.

Слушает только `10.66.66.1:10000` (AWG-релей). В публичный интернет не публиковать.

```bash
sudo mkdir -p /etc/sing-box
sudo cp sing-box-vless.json /etc/sing-box/config.json
# подставить UUID и SECRET_PATH (совпадает с Caddyfile)
uuidgen
openssl rand -hex 16
sudo sing-box check -c /etc/sing-box/config.json
sudo systemctl enable --now sing-box
sudo systemctl status sing-box
ss -lntp | grep 10000
```

Пример unit (`/etc/systemd/system/sing-box.service`):

```ini
[Unit]
Description=sing-box VLESS WebSocket
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=3
LimitNOFILE=1048576

[Install]
WantedBy=multi-user.target
```

## Happ (первый клиент вручную)

| Поле | Значение |
| --- | --- |
| Address | `resume.sde-lab.ru` |
| Port | `443` |
| UUID | из конфига |
| Encryption | `none` |
| Transport | `ws` |
| Path | `/REPLACE_SECRET_PATH` |
| SNI / Host | `resume.sde-lab.ru` |
| TLS | включён |

```text
vless://UUID@resume.sde-lab.ru:443?encryption=none&security=tls&sni=resume.sde-lab.ru&type=ws&host=resume.sde-lab.ru&path=%2FREPLACE_SECRET_PATH#iphone-1
```
