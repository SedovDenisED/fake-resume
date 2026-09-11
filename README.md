# README

Фасад `resume.sde-lab.ru` + вход Happ (VLESS/XHTTP) через Yandex Cloud на домашний сервер.

См. [plan.md](plan.md).

## Каталоги

| Путь | Назначение |
| --- | --- |
| `facade/` | Статический лендинг (Caddy на YC) |
| `deploy/yc/` | Caddy, AWG peer, DNAT 51820 |
| `deploy/home/` | sing-box VLESS/XHTTP |
| `panel/` | FastAPI-панель клиентов Happ |

## Локальный просмотр лендинга

```bash
cd facade && python3 -m http.server 8765
```

Открыть http://127.0.0.1:8765/
