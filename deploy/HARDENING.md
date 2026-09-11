# Автозапуск и секреты (пункты 1–3)

## 1. Автозапуск

Юниты копировать вручную на машины (репо на дом можно не клонировать).

### Дом
Файл `/etc/systemd/system/awg-relay.service` — см. `deploy/home/awg-relay.service`
(идемпотентный down/up + `ExecStartPost=systemctl --no-block restart sing-box`).

В `/etc/amnezia/amneziawg/awg-relay.conf` — только ip rule для `10.66.66.0/24`.
**Не** ставь `PostUp = systemctl restart sing-box` (дедлок с `After=awg-relay`).

sing-box override:
```ini
[Unit]
After=awg-relay.service
Wants=awg-relay.service

[Service]
User=root
Group=root
Restart=on-failure
RestartSec=5
```

### YC
```bash
sudo systemctl disable --now awgyc.service   # если ещё не
sudo cp ~/awg-relay.service /etc/systemd/system/awg-relay.service
# или scp с дома: deploy/yc/awg-relay.service
sudo cp ~/yc-dns-pin.service /etc/systemd/system/yc-dns-pin.service
sudo systemctl daemon-reload
sudo systemctl enable --now awg-relay.service
sudo systemctl enable --now yc-dns-pin.service
sudo systemctl enable --now caddy
systemctl is-enabled awg-relay yc-dns-pin caddy
```

Проверка после ребута YC (preemptible): сайт HTTPS, `ping 10.66.66.1`, Happ.

## 2. DNS на YC

Сервис `yc-dns-pin.service` после boot снова ставит DNS на eth0.
Убедись, что `awgyc.service` disabled и `awgyc.conf` переименован в `.disabled`.

```bash
resolvectl query github.com
```

## 3. Ключи не в git

- Боевые ключи только в `/etc/amnezia/amneziawg/awg-relay.conf` на машинах.
- В репо `deploy/*/awg-relay.conf` — только `REPLACE_*`.
- Если в локальном клоне `~/fake-resume/deploy/**/awg-relay.conf` когда-то вписал ключи:

```bash
cd ~/fake-resume
git checkout -- deploy/home/awg-relay.conf deploy/yc/awg-relay.conf
# или скопируй шаблоны заново с REPLACE_
```

Ротация тестовых ключей — отдельным шагом позже (новые genkey, правка /etc на обеих сторонах, down/up).
