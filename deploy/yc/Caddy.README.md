# Caddy на YC: лендинг + TLS + proxy VLESS/XHTTP на дом

Домен: resume.sde-lab.ru (Cloudflare DNS Only → IP YC).

Статика — ветка `facade` (в корне `index.html`, без panel/deploy):

```bash
git clone --branch facade --single-branch git@github-second:SedovDenisED/fake-resume.git /var/www/resume
# обновление:
cd /var/www/resume && git pull
```

```bash
sudo apt install -y caddy   # или официальный репозиторий Caddy
sudo cp Caddyfile /etc/caddy/Caddyfile
# Вписать тот же SECRET_PATH, что в sing-box на доме
sudo systemctl enable --now caddy
sudo systemctl reload caddy
```

В Caddyfile `root * /var/www/resume` (корень ветки facade).

Проверки:

```bash
curl -sI https://resume.sde-lab.ru/ | head
curl -sI "https://resume.sde-lab.ru/wrong-path" | head
```

Ожидание: лендинг 200; чужой path — 404 от Caddy или лендинг (не ответ xray/sing-box).
