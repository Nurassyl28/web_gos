# LMS Lite

Минимальный LMS на FastAPI + PostgreSQL с JWT, ролями и простым фронтом.

## Структура
- `app/` – FastAPI-приложение с разделением `api`, `services`, `models`, `schemas` и `core`
- `alembic/` – миграции
- `tests/` – pytest с фикстурами и сценариями
- `static/` – простые HTML-страницы (вход и панель)
- `auth/register` – открытый эндпоинт для создания студента (role=student, поле в payload; попытки указать другую роль запрещены)
- `auth/login` – принимает JSON `{"email": "...", "password": "..."}`, возвращает JWT, теперь без зависимости от `python-multipart`.

## Быстрый запуск (разработка)
1. Перейдите в каталог проекта:
   ```bash
   cd lms_lite
   ```
2. Скопируйте `.env.example` в `.env` и заполните реальные значения (особенно `DATABASE_URL`, `SECRET_KEY`).
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите миграции:
   ```bash
   alembic upgrade head
   ```
5. Запустите сервер:
   ```bash
   uvicorn main:app --reload
   ```
6. Перейдите на `http://localhost:8000/static/index.html`.

## Тесты
```bash
cd lms_lite
pytest
```

## Docker
- Билд и запуск локально:
  ```bash
  docker compose up --build
  ```
- Postgres и FastAPI поднимаются вместе; web-сервис использует переменные окружения из `docker-compose.yml`.

## Миграции
- Инициализация/генерация:
  ```bash
  alembic revision --autogenerate -m "Имя"
  ```
- Применение:
  ```bash
  alembic upgrade head
  ```
- В окружении Docker, где `web` использует `PYTHONPATH=/code` и подключается к Postgres, можно запускать:
  ```bash
  docker compose run --rm -e PYTHONPATH=/code -e PGPASSWORD=postgres web alembic upgrade head
  ```

## Тестовые аккаунты (фиксированные для тестов)
- Admin: `admin@example.com` / `safe_pass123`
- Student: `student@example.com` / `safe_pass123`

## Роль и безопасность
- JWT-токены подписываются секретом из `.env`
- Пароли хэшируются через `bcrypt`
- Админские эндпоинты защищены зависимостями `get_current_admin`
- Пагинация и фильтрация курсов с ограничением `limit <= 100`
# web_gos
