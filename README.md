# Лабораторная работа №1 — защищённый REST API

Учебный REST API на **Python 3.11, Flask и SQLite** с автоматической проверкой безопасности в GitHub Actions: SAST (Bandit) и SCA (pip-audit).

## Стек

- Python 3.11, Flask 3.1
- Flask-SQLAlchemy (ORM), SQLite
- Flask-JWT-Extended (JWT), bcrypt
- MarkupSafe (экранирование вывода)
- GitHub Actions: Bandit, pip-audit

## Запуск

Все команды выполняются из папки `lab1`:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # задать свои SECRET_KEY и JWT_SECRET_KEY
python app.py                      # API на http://127.0.0.1:9091
```

Секреты читаются только из переменных окружения или файла `.env`, который не добавляется в Git. Если `JWT_SECRET_KEY` не задан, при старте генерируется случайный ключ: тогда после перезапуска старые токены перестают действовать. База `securedb.db` создаётся автоматически.

## API

| Метод | Путь | Тело JSON | Результат |
|------|----------------|------------------|------------------------------|
| POST | `/auth/register` | `login`, `password` | Регистрация, JWT, HTTP 201 |
| POST | `/auth/login` | `login`, `password` | JWT, HTTP 200 |
| GET | `/api/data` | — | Список данных, только с JWT |

Логин и пароль должны быть длиной 5–50 символов. Ошибки: `400` — неверные поля, `409` — пользователь уже существует, `401` — неверный логин или пароль.

`GET /api/data` требует заголовок `Authorization: Bearer <JWT>`. Если токен отсутствует, подделан или просрочен, сервер возвращает `401`. Токен действует 15 минут.

### Проверка через curl

```bash
curl -i http://127.0.0.1:9091/api/data
# Ожидается 401 {"error": "Unauthorized"}

curl -s http://127.0.0.1:9091/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"login":"alice","password":"S3cure-Pass"}'
# Ожидается 201 {"access_token": "..."}

curl -s http://127.0.0.1:9091/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"alice","password":"S3cure-Pass"}'
# Ожидается 200 {"access_token": "eyJhbGciOiJIUzI1NiIs..."}
export TOKEN='полученный_access_token'

curl -i http://127.0.0.1:9091/api/data \
  -H "Authorization: Bearer $TOKEN"
# Ожидается 200 [{"id": 1, "data": "..."}]

curl -i http://127.0.0.1:9091/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"login":"alice","password":"wrong"}'
# Ожидается 401 {"error": "Incorrect password"}
```

## Меры защиты

- **SQLi:** все запросы к базе выполняются через ORM SQLAlchemy (`db.session.get`, `Model.query`, `db.session.add`). ORM передаёт значения в SQLite отдельными параметрами, поэтому ввод вида `alice' --` не меняет запрос. Конкатенации пользовательского ввода в SQL нет.

```python
user = db.session.get(AuthModel, login)
```

- **XSS:** пользовательские данные экранируются через `markupsafe.escape` перед сохранением логина и при каждой выдаче данных в `/api/data`. Нагрузка `<script>alert(1)</script>` возвращается как `&lt;script&gt;alert(1)&lt;/script&gt;`. API отвечает только JSON.

```python
return jsonify([
    {'id': p.id, 'data': str(escape(p.data))}
    for p in products
]), 200
```

- **Пароли:** хранятся только как хэши **bcrypt** со случайной солью и cost-фактором 12. Проверка выполняется через `bcrypt.checkpw`. Пароль длиннее 72 байт отклоняется, так как bcrypt не обрабатывает такие пароли.

```python
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()
```

- **JWT:** после успешного входа или регистрации выдаётся токен, подписанный HMAC-SHA256. Срок действия — 15 минут. Ключ задаётся переменной `JWT_SECRET_KEY` и не хранится в коде.
- **Middleware:** декоратор `@jwt_required()` из Flask-JWT-Extended проверяет на защищённых эндпоинтах наличие токена, его подпись и срок действия. При ошибке сервер возвращает `401`.

```python
@api_bp.route('/data', methods=['GET'])
@jwt_required()
def get_data():
```

- **Сервер:** по умолчанию слушает только `127.0.0.1`, режим отладки выключен.

## CI/CD

Конфигурация находится в `.github/workflows/ci.yml` в корне репозитория, команды выполняются в папке `lab1`. Pipeline запускается при каждом `push` и `pull request`. В нём два job:

| Job | Инструмент | Что делает | Когда падает |
|---------------|---------|------------------------------|---------------|
| SAST — Bandit | Bandit | Статический анализ кода Python | Находка уровня Medium или High |
| SCA — pip-audit | pip-audit | Проверка зависимостей из `requirements.txt`, включая транзитивные, по базе уязвимостей PyPI/OSV | Любая известная уязвимость |

Итоги проверок выводятся в Summary запуска, JSON-отчёты сохраняются в artifacts `bandit-report` и `pip-audit-report`.

### Исправленные уязвимости

Первая проверка pip-audit нашла уязвимости в зависимостях: `flask 3.0.3` (PYSEC-2026-2151) и `python-dotenv 1.0.1` (PYSEC-2026-2270). Зависимости обновлены до `Flask 3.1.3` и `python-dotenv 1.2.4`, остальные — до актуальных версий.

Bandit нашёл B104 (Medium): сервер слушал все интерфейсы `0.0.0.0`. Теперь по умолчанию используется `127.0.0.1`, адрес задаётся переменной `HOST`.

## Скриншоты отчётов SAST/SCA

![Pipeline](screenshots/pipeline.png)

![Bandit](screenshots/bandit.png)

![pip-audit](screenshots/pip-audit.png)
