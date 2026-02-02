"""
Бэкенд аутентификации по JSON-файлу admins.json вместо SQLite auth_user.
Пароли хранятся в открытом виде. Сессии в БД; в сессии сохраняем admin_username.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

from core import storage

# Один «прокси»-пользователь в БД для сессии (id=1). Создаётся в init_admin.
PROXY_USERNAME = "__admin_proxy__"


class JSONFileBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username:
            return None
        admin = storage.get_admin_by_username(username)
        if not admin:
            return None
        stored_password = admin.get("password") or ""
        if (password or "") != stored_password:
            return None
        if not admin.get("is_staff", True):
            return None
        User = get_user_model()
        try:
            proxy = User.objects.get(username=PROXY_USERNAME)
        except User.DoesNotExist:
            return None
        if request is not None:
            request.session["admin_username"] = username
            request.session["role"] = admin.get("role") or "admin"
            request.session["group_id"] = admin.get("group_id") or ""
        return proxy

    def get_user(self, user_id):
        User = get_user_model()
        try:
            user = User.objects.get(pk=user_id)
            if user.username == PROXY_USERNAME:
                return user
        except User.DoesNotExist:
            pass
        return None
