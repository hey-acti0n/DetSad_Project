#!/usr/bin/env python
"""Создать прокси-пользователя в БД, админа (admin/1111), 10 групп (1..10) и 10 воспитателей (teremok1..teremok10).

- Админ: полный доступ.
- Воспитатель teremokN: доступ только к группе N (groupN). Пароль совпадает с логином (teremok1, teremok2, ...).
Запуск: python scripts/init_admin.py
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model

from api.auth_backend import PROXY_USERNAME
from core import storage

User = get_user_model()

# 1. Прокси-пользователь в БД (нужен для сессии Django)
proxy, _ = User.objects.get_or_create(
    username=PROXY_USERNAME,
    defaults={"email": "", "is_staff": True, "is_superuser": False},
)
proxy.is_staff = True
proxy.save(update_fields=["is_staff"])

# 2. Десять групп: group1..group10 с названиями «1»..«10»
storage.ensure_groups_numbered(10)

# 3. Админ (полный доступ)
storage.add_or_update_admin("tusikbuch", "10055055", is_staff=True, role="admin")

# 4. Десять воспитателей: teremok1/teremok1 → group1, teremok2/teremok2 → group2, ...
for n in range(1, 11):
    login = f"teremok{n}"
    storage.add_or_update_admin(login, login, is_staff=True, role="educator", group_id=f"group{n}")
