# DealHunter

Веб-сервис для анализа скидок и истории цен на игры. Подробное описание идеи, ролей и схемы данных — см. [TZ.md](TZ.md).

> Статус: в разработке.

## Стек

- Python 3.12, Django 5.x
- IsThereAnyDeal API v2 (requests)
- Pandas — расчёт индекса выгодности (Deal Score)
- Plotly — графики истории цен
- Bootstrap 5
- SQLite (разработка)

## Локальный запуск

```bash
git clone <repo-url>
cd dealhunter
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # заполнить SECRET_KEY и ITAD_API_KEY
python manage.py migrate
python manage.py runserver
```

## Деплой

См. инструкцию в TZ.md / описание ниже (будет дополнено).
