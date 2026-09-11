# AmneziaWG: peer на Yandex Cloud (сервер↔дом)

Интерфейс отдельно от клиентского DNAT `51820`.
Подсеть релея по умолчанию: `10.66.66.0/24` (YC = `.2`, дом = `.1`).

## Установка (YC)

```bash
# AmneziaWG kernel module + tools (как у тебя принято на доме)
sudo mkdir -p /etc/amnezia/amneziawg
sudo cp awg-relay.conf /etc/amnezia/amneziawg/awg-relay.conf
sudo chmod 600 /etc/amnezia/amneziawg/awg-relay.conf
sudo awg-quick up awg-relay
```

Сгенерировать ключи:

```bash
awg genkey | tee /tmp/yc_private.key | awg pubkey > /tmp/yc_public.key
```

Подставить `PrivateKey` сюда и `PublicKey` домашнего пира в `[Peer]`.
`Endpoint` дома — не нужен на YC, если дом инициирует handshake (см. home peer с `Endpoint = YC_IP:51821`).

Порт `51821/udp` открыть только для домашнего ISP IP (или временно 0.0.0.0, затем сузить).

## systemd (пример)

```ini
[Unit]
Description=AmneziaWG relay YC-home
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/bin/awg-quick up awg-relay
ExecStop=/usr/bin/awg-quick down awg-relay

[Install]
WantedBy=multi-user.target
```
