# Архитектура: YC (фасад + релей) → домашний сервер

## Цель

Стабильный вход с 3–4 iPhone (Happ) для Telegram и иногда YouTube Shorts.
Мобильный оператор видит обычный HTTPS на `resume.sde-lab.ru` (белый IP Yandex Cloud).
Вся маршрутизация, DNS (AGH), AWG→FI и панель управления — **только дома**.

## Структура репозитория

```text
facade/          # статический лендинг для Caddy на YC
deploy/yc/       # Caddyfile, AWG peer, DNAT 51820
deploy/home/     # sing-box VLESS/XHTTP
panel/           # FastAPI: клиенты Happ, QR/ссылки, логи
```

Исходник Django [`sde-resume`](../sde-resume) **не меняем** — из него взят только лендинг (без заявок, about/library/project).

## Решение по транспорту

| Было | Станет |
| --- | --- |
| AmneziaWG → `YC:51820/udp` → DNAT → дом `awg1` | Happ → `resume.sde-lab.ru:443` (VLESS + WebSocket) → дом |
| Нестабильно в части локаций | UDP `51820` остаётся **резервом** |

## Схема трафика

```text
[ iPhone + Happ ]
       |
       | HTTPS TCP 443 / TLS (SNI: resume.sde-lab.ru)
       | VLESS + WebSocket, секретный path
       v
[ Yandex Cloud VPS ]  IP постоянный, preemptible (+ авторестарт)
       |
       |-- обычный посетитель / probe --> статика лендинга (facade/)
       |-- VLESS path -----------------> reverse_proxy через AWG
       |-- UDP 51820 (резерв) ---------> DNAT + MASQUERADE --> дом awg1
       |
       | AWG server-server (YC <-> дом)
       v
[ Домашний MiniPC ]
       |-- VLESS inbound (только с AWG/YC)
       |-- AGH + существующая маршрутизация (не трогаем)
       |-- AWG --> FI VPS (как сейчас)
       +-- Python-панель (только изнутри туннеля)
```

## Компоненты

### DNS / TLS

- Cloudflare: `resume.sde-lab.ru` A → IP YC, **DNS Only**.
- Сертификат Let's Encrypt на **YC** (Caddy).

### YC

- Caddy: `:443` + `facade/`, proxy секретного path → дом по AWG.
- AWG peer до дома (отдельно от клиентского `51820`).
- DNAT UDP `51820` + обновление домашнего IP — резерв.

### Дом

- sing-box: VLESS + WebSocket (только с YC по AWG; официальный sing-box без xhttp).
- FastAPI-панель: клиенты Happ, QR/ссылка, логи.
- Первый клиент — вручную с дома.

### Клиенты

- iOS, Happ: Address/SNI `resume.sde-lab.ru`, Port `443`, WebSocket, секретный path.

### Скрытый вход в панель

- 5 быстрых кликов по логотипу SDE на лендинге → URL панели в AWG-сети.

## Важно

- Не включать оранжевое облако Cloudflare.
- Секретный path — длинный случайный.
- VLESS на доме не публиковать в интернет.
- Алерты не нужны; только логи.
