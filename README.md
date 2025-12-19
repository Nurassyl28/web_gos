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

# Роль и безопасность
- JWT-токены подписываются секретом из `.env`
- Пароли хэшируются через `bcrypt`
- Админские эндпоинты защищены зависимостями `get_current_admin`
- Пагинация и фильтрация курсов с ограничением `limit <= 100`

## Дополнительные детали курсов
- Каждому курсу теперь можно задать `level` (`beginner`, `intermediate`, `advanced`) и `duration_minutes`, эти поля возвращаются в ответах `/courses` и используются при создании/редактировании.
- Публичный эндпоинт `GET /courses/levels` отдает список доступных уровней с пояснениями, чтобы UI мог показать уточненную классификацию.

## Задания и материалы
- Преподаватель (администратор) может создавать задания под курсами через `POST /assignments/courses/{course_id}` и обновлять/удалять их через `PUT /assignments/{id}` и `DELETE /assignments/{id}`.
- Студенты видят только задания курсов, в которые они записаны, через `GET /assignments`. Админ может просматривать весь список.
- Чтобы отобразить задания в UI, используйте `GET /assignments/courses/{course_id}` (для админа или записанного студента); в ответе возвращаются `title`, `description`, `link`, `due_date`.
- Студенты отправляют ответы на задания через `POST /assignments/{assignment_id}/submit` (обязательное поле `message`, опционально `link`) и могут просматривать свои ответы через `GET /assignments/submissions`.
- Админ получает от студентов список решений конкретного задания через `GET /assignments/{assignment_id}/submissions`.
- Админ может видеть все ответы сразу через `GET /assignments/admin-overview`, в ответе приходит кто, для какого курса и задания отправил решение.

## Auth и безопасность
- Авторизация: `POST /auth/login` возвращает `access_token` и `refresh_token`. `POST /auth/refresh` обновляет пару токенов, `POST /auth/logout` отзывает refresh.
- Схема обеспечивает role-based доступ (admin/student) и защиту от bruteforce: одноимённый middleware лимитирует запросы, а на уровне логина отслеживаются попытки.
- Включено логирование успешных логинов/логаутов, rate limiting, проверка HTTPS (по `REQUIRE_HTTPS`), контроль размера запросов (`MAX_REQUEST_SIZE`) и CORS по списку `CORS_ORIGINS`.

## Дополнительные переменные окружения
- `CORS_ORIGINS` — список разрешённых origin через запятую (по умолчанию разрешены все).
- `REQUIRE_HTTPS` — принудительный редирект/отказ при HTTP.
- `RATE_LIMIT_REQUESTS`, `RATE_LIMIT_WINDOW_SECONDS` — rate limiting по IP (по умолчанию 120 запросов в минуту).
- `MAX_REQUEST_SIZE` — максимальный размер тела запроса в байтах.
- `LOGIN_ATTEMPTS_LIMIT`, `LOGIN_ATTEMPTS_WINDOW_SECONDS` — ограничения на попытки логина (по умолчанию 5 попыток за 5 минут).
- `REFRESH_TOKEN_EXPIRE_MINUTES` — срок жизни refresh-токена (по умолчанию неделя).
# web_gos
