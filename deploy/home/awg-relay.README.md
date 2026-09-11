# AmneziaWG: peer на домашнем MiniPC (сервер↔YC)

```bash
sudo mkdir -p /etc/amnezia/amneziawg
sudo cp awg-relay.conf /etc/amnezia/amneziawg/awg-relay.conf
sudo chmod 600 /etc/amnezia/amneziawg/awg-relay.conf
sudo awg-quick up awg-relay
ping -c3 10.66.66.2
```

`Endpoint` = публичный IP YC и порт `51821`.
Дом инициирует handshake (удобно при динамическом домашнем IP).

Клиентский `awg1` на `51820` не трогаем.
