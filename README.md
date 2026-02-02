# Эко-сад — веб-приложение для детского сада

Мини-игра с эко-монетами: дети выбирают себя на главной странице, взаимодействуют с объектами (кран, коробка, метла), получают анимацию и начисление монет. Администратор входит в панель и просматривает статистику.

## Стек

- **Frontend:** React 18, React Router, Vite
- **Backend:** Django 5, Django REST Framework
- **Хранение:** JSON-файлы (группы, дети, события) + SQLite для авторизации админа

## Запуск локально (без Docker)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python scripts/init_admin.py   # создаёт admin / admin
python manage.py runserver
```

API: http://localhost:8000

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Приложение: http://localhost:5173 (прокси на backend настроен в `vite.config.js`).

**Вход в админку:** http://localhost:5173/admin-login — логин `admin`, пароль `admin`.

---

## Запуск в Docker (staging/production)

Сборка для **linux/amd64** (совместимость с ВМ в Yandex Cloud):

```bash
docker compose build
docker compose up -d
```

Приложение: http://localhost (порт 80).  
Админка: http://localhost/admin-login (логин `admin`, пароль `admin`).

Для production задайте переменные окружения:

- `DJANGO_SECRET_KEY` — секретный ключ Django
- В `docker-compose.yml` в `ALLOWED_HOSTS` и `CORS_ORIGINS` укажите ваш домен

---

## Развёртывание в Yandex Cloud

Подробная пошаговая инструкция: **[DEPLOY_YANDEX.md](DEPLOY_YANDEX.md)**.

**Вариант с одним контейнером (Docker Hub):** можно собрать один образ со всем приложением, выложить в Docker Hub и на ВМ только выполнить `docker run` (без копирования кода). В корне проекта:

```bash
docker build --platform linux/amd64 -t ВАШ_ЛОГИН/detsad:latest .
docker push ВАШ_ЛОГИН/detsad:latest
```

На ВМ: установите Docker, создайте `.env` с `DJANGO_SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ORIGINS`, затем `docker run -d -p 8000:8000 --env-file .env ВАШ_ЛОГИН/detsad:latest`. Подробности — разделы **3а** и **5а** в DEPLOY_YANDEX.md.

**Вариант с docker-compose (два контейнера):**
1. Создайте ВМ в Yandex Cloud (Ubuntu 22.04), откройте порт 80.
2. Установите Docker и Docker Compose на ВМ.
3. Скопируйте проект на ВМ, создайте `.env` из `.env.example`, задайте `ALLOWED_HOSTS` и `CORS_ORIGINS` (IP или домен).
4. Запустите: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d`.
5. Откройте в браузере: `http://<ПУБЛИЧНЫЙ_IP>`. Для домена и HTTPS см. раздел 7 в DEPLOY_YANDEX.md.

---

## Структура проекта

```
DetSad/
├── backend/           # Django API
│   ├── config/         # settings, urls
│   ├── api/            # views, urls API
│   ├── core/           # storage.py — работа с JSON
│   ├── data/           # groups.json, children.json, events.json, db.sqlite3
│   ├── scripts/        # init_admin.py
│   └── Dockerfile
├── frontend/           # React SPA
│   ├── src/
│   │   ├── pages/      # Home, AdminLogin, AdminPanel
│   │   ├── components/ # ChildCards, GameScene
│   │   └── api.js
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API (кратко)

- `GET /api/v1/children` — список детей
- `POST /api/v1/game/interaction` — тело `{ "childId", "actionId" }` (crane / box / broom)
- `POST /api/v1/admin/login` — логин админа
- `GET /api/v1/admin/stats/groups`, `GET /api/v1/admin/stats/children`, `GET /api/v1/admin/child/:id/events`, `POST /api/v1/admin/child/:id/balance-adjust` и др.

Правила начисления и лимиты задаются в `backend/data/actions_config.json` (и создаются по умолчанию при первом запуске).
