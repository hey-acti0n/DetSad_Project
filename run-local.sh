#!/bin/bash
# Запуск приложения локально. Выполните в терминале: ./run-local.sh

set -e
cd "$(dirname "$0")"

echo "=== Backend ==="
cd backend
if [ ! -d venv ]; then
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt
python manage.py migrate --noinput 2>/dev/null || true
python scripts/init_admin.py 2>/dev/null || true
echo "Backend запускается на http://127.0.0.1:8000"
python manage.py runserver &
BACKEND_PID=$!
cd ..

echo "=== Frontend ==="
cd frontend
if [ ! -d node_modules ]; then
  npm install
fi
echo "Frontend запускается на http://127.0.0.1:5173"
npm run dev &
FRONTEND_PID=$!
cd ..

cleanup() { kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0; }
trap cleanup SIGINT SIGTERM

echo ""
echo "Приложение: http://localhost:5173"
echo "Админка: http://localhost:5173/admin-login (логин: admin, пароль: admin)"
echo "Остановка: Ctrl+C"
wait
