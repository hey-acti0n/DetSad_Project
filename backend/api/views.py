from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie

from core import storage


def _educator_group_id(request):
    """Группа воспитателя (если вошёл воспитатель). Иначе None."""
    if request.session.get("role") == "educator":
        return request.session.get("group_id") or None
    return None


@api_view(["GET"])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_set(request):
    """Установить CSRF cookie для SPA."""
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([AllowAny])
def groups_list(request):
    """GET /api/v1/groups — список групп (id, name) для выбора на первом экране."""
    groups = storage.get_groups()
    return Response([{"id": g["id"], "name": g.get("name", g["id"])} for g in groups])


@api_view(["GET"])
@permission_classes([AllowAny])
def children_list(request):
    """GET /api/v1/children — список детей (id, fullName, groupId, balance)."""
    children = storage.get_children()
    return Response([{"id": c["id"], "fullName": c.get("fullName", ""), "groupId": c.get("groupId"), "balance": c.get("balance", 0), "avatar": c.get("avatar")} for c in children])


@api_view(["GET"])
@permission_classes([AllowAny])
def game_actions(request):
    """GET /api/v1/game/actions — правила начисления (id, name, coins, cooldown_sec, daily_limit_coins)."""
    actions = storage.get_actions_config()
    return Response(actions)


@api_view(["POST"])
@permission_classes([AllowAny])
def game_interaction(request):
    """POST /api/v1/game/interaction — взаимодействие: body { childId, actionId }."""
    child_id = request.data.get("childId")
    action_id = request.data.get("actionId")
    if not child_id or not action_id:
        return Response({"success": False, "reason": "childId and actionId required"}, status=status.HTTP_400_BAD_REQUEST)
    result = storage.process_interaction(child_id, action_id)
    return Response(result)


# --- Admin (session auth) ---

@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([SessionAuthentication])
def admin_login(request):
    """POST /api/v1/admin/login — логин, выдаёт сессию (cookie)."""
    username = request.data.get("username")
    password = request.data.get("password")
    if not username or not password:
        return Response({"ok": False, "error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"ok": False, "error": "invalid_credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    if not user.is_staff:
        return Response({"ok": False, "error": "not_staff"}, status=status.HTTP_403_FORBIDDEN)
    login(request, user)
    return Response({"ok": True})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_logout(request):
    """POST /api/v1/admin/logout."""
    logout(request)
    return Response({"ok": True})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_me(request):
    """GET /api/v1/admin/me — роль и группа текущего пользователя (для воспитателя)."""
    role = request.session.get("role") or "admin"
    group_id = request.session.get("group_id") or None
    return Response({"role": role, "group_id": group_id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_stats_groups(request):
    """GET /api/v1/admin/stats/groups?from=...&to=..."""
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    data = storage.get_stats_groups(from_date=from_date, to_date=to_date)
    group_id = _educator_group_id(request)
    if group_id:
        data = [g for g in data if g.get("groupId") == group_id]
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_stats_children(request):
    """GET /api/v1/admin/stats/children?groupId=...&q=...&from=...&to=..."""
    group_id = _educator_group_id(request) or request.query_params.get("groupId")
    q = request.query_params.get("q")
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    data = storage.get_stats_children(group_id=group_id, q=q, from_date=from_date, to_date=to_date)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_child_events(request, id):
    """GET /api/v1/admin/child/:id/events?from=...&to=... Воспитатель — только дети своей группы."""
    educator_group = _educator_group_id(request)
    if educator_group:
        child = storage.get_child_by_id(id)
        if not child or child.get("groupId") != educator_group:
            return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    data = storage.get_all_events(child_id=id, from_date=from_date, to_date=to_date)
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_balance_adjust(request, id):
    """POST /api/v1/admin/child/:id/balance-adjust — body { delta, comment }."""
    group_id = _educator_group_id(request)
    if group_id:
        child = storage.get_child_by_id(id)
        if not child or child.get("groupId") != group_id:
            return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
    delta = request.data.get("delta")
    comment = request.data.get("comment", "")
    if delta is None:
        return Response({"error": "delta required"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        delta = int(delta)
    except (TypeError, ValueError):
        return Response({"error": "delta must be integer"}, status=status.HTTP_400_BAD_REQUEST)
    admin_username = request.session.get("admin_username") or getattr(request.user, "username", "")
    new_balance = storage.adjust_balance(id, delta, comment, admin_username)
    if new_balance is None:
        return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response({"new_balance": new_balance})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_events(request):
    """GET /api/v1/admin/events?groupId=...&childId=...&from=...&to=..."""
    group_id = _educator_group_id(request) or request.query_params.get("groupId")
    child_id = request.query_params.get("childId")
    from_date = request.query_params.get("from")
    to_date = request.query_params.get("to")
    data = storage.get_all_events(group_id=group_id, child_id=child_id, from_date=from_date, to_date=to_date)
    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_monthly_results(request):
    """GET /api/v1/admin/monthly-results — итоги по месяцам (после сброса баланса)."""
    group_id = _educator_group_id(request)
    data = storage.get_monthly_results(group_id=group_id)
    return Response(data)


# --- CRUD групп ---

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_groups_list(request):
    """GET /api/v1/admin/groups — список групп для управления."""
    data = storage.get_groups()
    group_id = _educator_group_id(request)
    if group_id:
        data = [g for g in data if g.get("id") == group_id]
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_group_create(request):
    """POST /api/v1/admin/groups — создать группу. Воспитателю запрещено."""
    if _educator_group_id(request):
        return Response({"error": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
    name = request.data.get("name", "").strip()
    gid = storage.create_group(name)
    if gid:
        return Response({"id": gid, "name": name or "Новая группа"}, status=status.HTTP_201_CREATED)
    return Response({"error": "invalid"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH", "DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_group_detail(request, id):
    """PUT /api/v1/admin/group/:id — обновить. DELETE — удалить. Воспитатель: только свою группу, удалять нельзя."""
    group_id = _educator_group_id(request)
    if request.method == "DELETE":
        if group_id:
            return Response({"error": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        result = storage.delete_group(id)
        if result is True:
            return Response({"ok": True})
        return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)
    if request.method in ("PUT", "PATCH"):
        if group_id and id != group_id:
            return Response({"error": "forbidden"}, status=status.HTTP_403_FORBIDDEN)
        name = request.data.get("name", "").strip()
        if storage.update_group(id, name):
            return Response({"id": id, "name": name})
        return Response({"error": "group not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


# --- CRUD детей ---

@api_view(["POST"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_child_create(request):
    """POST /api/v1/admin/children — создать ребёнка. Воспитатель может только в свою группу."""
    educator_group = _educator_group_id(request)
    group_id = request.data.get("groupId") or None
    if educator_group:
        group_id = educator_group
    full_name = request.data.get("fullName", "").strip()
    cid = storage.create_child(full_name, group_id)
    if cid:
        return Response({"id": cid, "fullName": full_name or "Без имени", "groupId": group_id}, status=status.HTTP_201_CREATED)
    return Response({"error": "invalid group"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "PATCH"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_child_update(request, id):
    """PUT /api/v1/admin/child/:id — обновить ребёнка. Воспитатель — только детей своей группы, groupId не менять."""
    educator_group = _educator_group_id(request)
    if educator_group:
        child = storage.get_child_by_id(id)
        if not child or child.get("groupId") != educator_group:
            return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
        group_id = educator_group
    else:
        group_id = request.data.get("groupId") if request.data.get("groupId") else None
    full_name = request.data.get("fullName", "").strip()
    if storage.update_child(id, full_name, group_id):
        return Response({"id": id, "fullName": full_name, "groupId": group_id})
    return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
@authentication_classes([SessionAuthentication])
def admin_child_delete(request, id):
    """DELETE /api/v1/admin/child/:id — удалить ребёнка. Воспитатель — только детей своей группы."""
    educator_group = _educator_group_id(request)
    if educator_group:
        child = storage.get_child_by_id(id)
        if not child or child.get("groupId") != educator_group:
            return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
    if storage.delete_child(id):
        return Response({"ok": True})
    return Response({"error": "child not found"}, status=status.HTTP_404_NOT_FOUND)
