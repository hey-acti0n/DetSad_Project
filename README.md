# Эко-сад

Веб-приложение для детского сада: мини-игра с эко-монетами («Экоши»). Дети выбирают себя на экране, выполняют экологичные действия (закрыть кран, сдать макулатуру, сортировать мусор и т.д.), получают начисление монет. Воспитатели и администратор заходят в панель управления: статистика по группам и детям, события, корректировка баланса, месячные итоги.

Подходит для планшетов и телефонов, работает как **PWA** (можно установить на домашний экран).

---

## Возможности

- **Детский интерфейс:** выбор группы → выбор ребёнка → игровая сцена с действиями (кран, макулатура, батарейки, крышки, сортировка). Начисление монет с кулдауном и дневным лимитом.
- **Дерево достижений:** общая страница «Наше дерево» по группе.
- **Админ-панель:** вход для администратора и воспитателей (доступ по группам). Статистика по группам и детям, журнал событий, корректировка баланса, месячные результаты и настройка действий.
- **Офлайн-режим:** PWA с кэшированием, можно добавить на экран и использовать при нестабильном интернете.

---

## Стек

| Часть      | Технологии |
|------------|------------|
| Frontend   | React 18, React Router, Vite, PWA (vite-plugin-pwa) |
| Backend    | Django 5, Django REST Framework, Gunicorn, WhiteNoise |
| Данные     | JSON-файлы (группы, дети, события, настройки действий, админы) + SQLite (сессии Django) |
| Развёртывание | Docker (один образ или docker-compose), Yandex Cloud |

---

## Быстрый старт

### Локально (без Docker)

**Backend:**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python scripts/init_admin.py
python manage.py runserver
```

API: **http://localhost:8000**

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

Приложение: **http://localhost:5173** (прокси на backend в `vite.config.js`).

**Вход в админку:**  
- Администратор: `tusikbuch` / `10055055`  
- Воспитатели: `teremok1` / `teremok1` … `teremok10` / `teremok10` (доступ к своей группе).  
Логины и пароли задаются в `backend/scripts/init_admin.py`.

---

### Docker (один контейнер)

В корне проекта:

```bash
docker build --platform linux/amd64 -t detsad:latest .
docker run -d -p 8000:8000 -v detsad-data:/app/data -e DJANGO_SECRET_KEY=your-secret -e ALLOWED_HOSTS=localhost,127.0.0.1 detsad:latest
```

Откройте **http://localhost:8000** (статика и API в одном контейнере).

---

### Docker Compose (frontend + backend)

```bash
docker compose build
docker compose up -d
```

Приложение: **http://localhost** (порт 80). Админка: **http://localhost/admin-login**.

---

## Развёртывание в облаке

Пошаговая инструкция по развёртыванию в **Yandex Cloud** (ВМ, один образ из Docker Hub или docker-compose, домен, HTTPS): **[DEPLOY_YANDEX.md](DEPLOY_YANDEX.md)**.

Рекомендуемые ресурсы ВМ для ~300 пользователей (по 2 действия в день): **2 ГБ RAM**, **15 ГБ диск**, 2 ядра. Подробный разбор — в разделе «Ресурсы ВМ» в DEPLOY_YANDEX.md.

---

## Структура проекта

```
DetSad/
├── backend/                 # Django API
│   ├── config/              # settings, urls
│   ├── api/                 # views, auth, urls API
│   ├── core/                # storage.py — работа с JSON (группы, дети, события)
│   ├── data/                # seed: groups.json, children.json и др.
│   ├── scripts/             # init_admin.py
│   ├── entrypoint.sh
│   └── requirements.txt
├── frontend/                # React SPA
│   ├── src/
│   │   ├── pages/           # GroupSelect, Play, OurTree, AdminLogin, AdminPanel
│   │   ├── components/
│   │   └── api.js
│   ├── index.html
│   └── vite.config.js
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile               # единый образ (frontend + backend)
├── DEPLOY_YANDEX.md
└── README.md
```

Данные в проде хранятся в томе Docker `detsad-data` → `/app/data` (JSON + `db.sqlite3`).

---

## API (кратко)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/v1/groups` | Список групп |
| GET | `/api/v1/children` | Список детей |
| GET | `/api/v1/game/actions` | Настройки действий (монеты, кулдаун, лимиты) |
| POST | `/api/v1/game/interaction` | Начисление за действие: `{ "childId", "actionId" }` |
| POST | `/api/v1/admin/login` | Вход в админку |
| GET | `/api/v1/admin/stats/groups`, `.../stats/children` | Статистика |
| GET | `/api/v1/admin/events` | Журнал событий с фильтрами |
| GET/POST | `/api/v1/admin/monthly-results`, `.../monthly-stats` | Месячные итоги |
| POST | `/api/v1/admin/child/<id>/balance-adjust` | Корректировка баланса |

Правила начисления (действия, монеты, кулдаун, дневной лимит) задаются в данных `actions_config` (по умолчанию создаются из `backend/data/` или из кода при первом запуске).

---

## PWA

После сборки (`npm run build`) приложение можно установить на устройство: «Добавить на экран» (Android) или «На экран Домой» (iOS). Иконки — в `frontend/public/` (замените на свои 192×192 и 512×512 px при необходимости).


