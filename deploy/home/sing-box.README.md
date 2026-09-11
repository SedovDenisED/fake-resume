# sing-box VLESS + XHTTP на доме

Слушает только `10.66.66.1:10000` (AWG-релей). В публичный интернет не публиковать.

```bash
# установка sing-box — по официальной инструкции под твою ОС
sudo mkdir -p /etc/sing-box
sudo cp sing-box-vless.json /etc/sing-box/config.json
# подставить UUID и SECRET_PATH (совпадает с Caddyfile)
uuidgen
sudo systemctl enable --now sing-box
sudo systemctl status sing-box
```

Пример unit (`/etc/systemd/system/sing-box.service`):

```ini
[Unit]
Description=sing-box VLESS XHTTP
After=network-online.target awg-quick@awg-relay.service
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

Исходящий трафик после VLESS идёт в `direct` — дальше твоя уже настроенная маршрутизация/AGH/FI на хосте. При необходимости замени outbound на существующий sing-box/xray стек (не входит в скоуп этого репо).

## Happ (первый клиент вручную)

| Поле | Значение |
| --- | --- |
| Address | `resume.sde-lab.ru` |
| Port | `443` |
| UUID | из конфига |
| Encryption | `none` |
| Transport | `xhttp` |
| Path | `/REPLACE_SECRET_PATH` |
| SNI / Host | `resume.sde-lab.ru` |
| TLS | включён |

Пример share-URI (после подстановки):

```text
vless://UUID@resume.sde-lab.ru:443?encryption=none&security=tls&sni=resume.sde-lab.ru&type=xhttp&path=%2FREPLACE_SECRET_PATH#iphone-1
```
