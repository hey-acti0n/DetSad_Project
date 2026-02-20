"""
Сервисный слой для хранения данных в JSON с файловыми блокировками.
"""
import json
import fcntl
import logging
import os
from pathlib import Path
from datetime import datetime, date, timedelta
from django.conf import settings

logger = logging.getLogger(__name__)

DATA_DIR = getattr(settings, "DATA_DIR", Path(__file__).resolve().parent.parent / "data")
DATA_DIR = Path(DATA_DIR)
DATA_DIR.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path(settings.SEED_DATA_DIR) if getattr(settings, "SEED_DATA_DIR", None) else None

FILES = {
    "groups": DATA_DIR / "groups.json",
    "children": DATA_DIR / "children.json",
    "events": DATA_DIR / "events.json",
    "actions_config": DATA_DIR / "actions_config.json",
    "monthly_results": DATA_DIR / "monthly_results.json",
    "last_month_reset": DATA_DIR / "last_month_reset.json",
    "admins": DATA_DIR / "admins.json",
}

DEFAULT_ACTIONS = [
    {"id": "crane", "name": "Закрытие крана", "coins": 1, "cooldown_sec": 120, "daily_limit_coins": 20},
    {"id": "cardboard_box", "name": "Макулатура", "coins": 5, "cooldown_sec": 120, "daily_limit_coins": 15},
    {"id": "battery", "name": "Батарейка", "coins": 5, "cooldown_sec": 120, "daily_limit_coins": 10},
    {"id": "plastic_cap", "name": "Пластиковые крышки", "coins": 3, "cooldown_sec": 120, "daily_limit_coins": 20},
    {"id": "sorting", "name": "Сортировка мусора", "coins": 2, "cooldown_sec": 120, "daily_limit_coins": 20},
]

DEFAULT_GROUPS = [{"id": "group1", "name": "Солнышко"}, {"id": "group2", "name": "Ромашка"}]
DEFAULT_CHILDREN = [
    {"id": "child1", "fullName": "Маша Иванова", "groupId": "group1", "balance": 0, "avatar": None},
    {"id": "child2", "fullName": "Петя Сидоров", "groupId": "group1", "balance": 0, "avatar": None},
    {"id": "child3", "fullName": "Аня Козлова", "groupId": "group2", "balance": 0, "avatar": None},
]


def _copy_from_seed(key):
    """Скопировать файл из каталога-семени (JSON из репозитория), если он есть."""
    if not SEED_DIR:
        return False
    seed_path = SEED_DIR / FILES[key].name
    if not seed_path.exists():
        return False
    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _write_json(key, data)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def _ensure_defaults():
    """Создать файлы с дефолтными данными, если их нет. Сначала пробуем скопировать из JSON репозитория (seed)."""
    if not FILES["groups"].exists():
        if not _copy_from_seed("groups"):
            _write_json("groups", DEFAULT_GROUPS)
    if not FILES["children"].exists():
        if not _copy_from_seed("children"):
            _write_json("children", DEFAULT_CHILDREN)
    if not FILES["events"].exists():
        if not _copy_from_seed("events"):
            _write_json("events", [])
    if not FILES["actions_config"].exists():
        if not _copy_from_seed("actions_config"):
            _write_json("actions_config", DEFAULT_ACTIONS)
    if not FILES["monthly_results"].exists():
        if not _copy_from_seed("monthly_results"):
            _write_json("monthly_results", [])
    if not FILES["last_month_reset"].exists():
        if not _copy_from_seed("last_month_reset"):
            _write_json("last_month_reset", {})
    if not FILES["admins"].exists():
        if not _copy_from_seed("admins"):
            _write_json("admins", [])


def reset_actions_config_to_defaults():
    """Перезаписать правила начисления очков: из seed (JSON репозитория) или из DEFAULT_ACTIONS."""
    _ensure_defaults()
    if not _copy_from_seed("actions_config"):
        _write_json("actions_config", DEFAULT_ACTIONS)


def _read_json(key):
    path = FILES[key]
    if not path.exists():
        _ensure_defaults()
    with open(path, "r", encoding="utf-8") as f:
        fd = f.fileno()
        fcntl.flock(fd, fcntl.LOCK_SH)
        try:
            f.seek(0)
            raw = f.read()
            return json.loads(raw) if raw.strip() else []
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def _write_json(key, data):
    path = FILES[key]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            json.dump(data, f, ensure_ascii=False, indent=2)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def get_groups():
    _ensure_defaults()
    return _read_json("groups")


def ensure_groups_numbered(count=10):
    """Обеспечить наличие групп group1..groupN с названиями «1»..«N». Не удаляет лишние группы."""
    _ensure_defaults()
    groups = get_groups()
    by_id = {g["id"]: g for g in groups}
    changed = False
    for i in range(1, count + 1):
        gid = f"group{i}"
        name = str(i)
        if gid not in by_id:
            groups.append({"id": gid, "name": name})
            by_id[gid] = {"id": gid, "name": name}
            changed = True
        elif by_id[gid].get("name") != name:
            for j, g in enumerate(groups):
                if g["id"] == gid:
                    groups[j] = {**g, "name": name}
                    break
            changed = True
    if changed:
        _write_json("groups", groups)


def _read_json_any(key, default=None):
    """Прочитать JSON; если ключа нет в FILES или файла нет — вернуть default."""
    if key not in FILES:
        return default
    path = FILES[key]
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        fd = f.fileno()
        fcntl.flock(fd, fcntl.LOCK_SH)
        try:
            f.seek(0)
            raw = f.read()
            return json.loads(raw) if raw.strip() else default
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def ensure_monthly_reset_done():
    """
    В конце месяца: при первом обращении в новом месяце сохранить итоги за прошлый месяц
    и обнулить балансы всех детей. Вызывать из get_children().
    """
    _ensure_defaults()
    now = datetime.now()
    now_year, now_month = now.year, now.month
    last = _read_json_any("last_month_reset")
    if last is None or not isinstance(last, dict):
        _write_json("last_month_reset", {"year": now_year, "month": now_month})
        return
    last_year, last_month = last.get("year"), last.get("month")
    if last_year is None or last_month is None or (now_year, now_month) <= (last_year, last_month):
        return
    # Новый месяц: сохраняем итоги за (last_year, last_month), обнуляем балансы
    children = _read_json("children")
    if not isinstance(children, list):
        _write_json("last_month_reset", {"year": now_year, "month": now_month})
        return
    snapshot = [
        {"childId": c["id"], "fullName": c.get("fullName", ""), "balance": c.get("balance", 0), "groupId": c.get("groupId")}
        for c in children
    ]
    total_sum = sum(s.get("balance", 0) for s in snapshot)
    results = _read_json_any("monthly_results") or []
    results.append({
        "year": last_year,
        "month": last_month,
        "children": snapshot,
        "totalSum": total_sum,
    })
    _write_json("monthly_results", results)
    for i in range(len(children)):
        children[i] = {**children[i], "balance": 0}
    _write_json("children", children)
    _write_json("last_month_reset", {"year": now_year, "month": now_month})


def get_children():
    try:
        _ensure_defaults()
        ensure_monthly_reset_done()
        data = _read_json("children")
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError, TypeError) as e:
        logger.warning("get_children failed: %s", e, exc_info=True)
        return []


def get_events():
    _ensure_defaults()
    return _read_json("events")


def get_actions_config():
    _ensure_defaults()
    return _read_json("actions_config")


def get_child_by_id(child_id):
    children = get_children()
    for c in children:
        if c["id"] == child_id:
            return c
    return None


def _event_date(ts):
    """Дата события (YYYY-MM-DD) для сравнения с периодом."""
    return (ts or "")[:10]


def get_events_for_child(child_id, from_date=None, to_date=None):
    events = get_events()
    out = [e for e in events if e.get("childId") == child_id]
    if from_date:
        out = [e for e in out if _event_date(e.get("timestamp")) >= from_date]
    if to_date:
        out = [e for e in out if _event_date(e.get("timestamp")) <= to_date]
    return sorted(out, key=lambda x: x.get("timestamp", ""), reverse=True)


def get_all_events(from_date=None, to_date=None, group_id=None, child_id=None):
    events = get_events()
    children = get_children()
    actions = get_actions_config()
    children_dict = {c["id"]: c.get("fullName", c["id"]) for c in children}
    actions_dict = {a["id"]: a.get("name", a["id"]) for a in actions}
    actions_dict["balance_adjust"] = "Корректировка баланса"
    if from_date:
        events = [e for e in events if _event_date(e.get("timestamp")) >= from_date]
    if to_date:
        events = [e for e in events if _event_date(e.get("timestamp")) <= to_date]
    if group_id:
        child_ids_in_group = {c["id"] for c in children if c.get("groupId") == group_id}
        events = [e for e in events if e.get("childId") in child_ids_in_group]
    if child_id:
        events = [e for e in events if e.get("childId") == child_id]
    # Добавляем ФИО ребёнка и название действия к каждому событию
    result = []
    for e in events:
        event = dict(e)
        event["childName"] = children_dict.get(e.get("childId"), e.get("childId"))
        event["actionName"] = actions_dict.get(e.get("actionId"), e.get("actionId"))
        result.append(event)
    return sorted(result, key=lambda x: x.get("timestamp", ""), reverse=True)


def _today_iso():
    return datetime.now().strftime("%Y-%m-%d")


def process_interaction(child_id, action_id):
    """
    Обработать взаимодействие: проверить cooldown и лимиты, начислить монеты, записать событие.
    Возвращает: {"success": bool, "credited": int, "new_balance": int, "reason": str}
    """
    _ensure_defaults()
    child = get_child_by_id(child_id)
    if not child:
        return {"success": False, "credited": 0, "new_balance": 0, "reason": "child_not_found"}

    actions = {a["id"]: a for a in get_actions_config()}
    action = actions.get(action_id)
    if not action:
        return {"success": False, "credited": 0, "new_balance": child["balance"], "reason": "unknown_action"}

    coins = action.get("coins", 0)
    cooldown_sec = action.get("cooldown_sec", 30)
    daily_limit = action.get("daily_limit_coins", 20)

    events = get_events()
    now = datetime.now()
    today = _today_iso()
    now_ts = now.isoformat()

    last_same_action = None
    daily_coins_for_action = 0
    for e in reversed(events):
        if e.get("childId") != child_id or e.get("actionId") != action_id:
            continue
        ts = e.get("timestamp", "")
        if ts.startswith(today):
            daily_coins_for_action += e.get("credited", 0)
        if last_same_action is None:
            last_same_action = ts

    if last_same_action:
        try:
            last_dt = datetime.fromisoformat(last_same_action.replace("Z", "+00:00"))
            if last_dt.tzinfo:
                last_dt = last_dt.replace(tzinfo=None)  # naive compare with now
        except (ValueError, TypeError):
            last_dt = now
        delta = (now - last_dt).total_seconds()
        if delta < cooldown_sec:
            return {
                "success": False,
                "credited": 0,
                "new_balance": child["balance"],
                "reason": "cooldown",
            }

    if daily_coins_for_action + coins > daily_limit:
        return {
            "success": False,
            "credited": 0,
            "new_balance": child["balance"],
            "reason": "daily_limit",
        }

    new_balance = child["balance"] + coins
    event = {
        "id": f"ev_{len(events) + 1}_{child_id}_{action_id}",
        "childId": child_id,
        "actionId": action_id,
        "credited": coins,
        "timestamp": now_ts,
        "balanceAfter": new_balance,
    }

    children = get_children()
    for i, c in enumerate(children):
        if c["id"] == child_id:
            children[i] = {**c, "balance": new_balance}
            break
    _write_json("children", children)

    events.append(event)
    _write_json("events", events)

    return {
        "success": True,
        "credited": coins,
        "new_balance": new_balance,
        "reason": "ok",
    }


def get_stats_groups(from_date=None, to_date=None):
    groups = get_groups()
    children = get_children()
    events = get_events()
    if from_date:
        events = [e for e in events if _event_date(e.get("timestamp")) >= from_date]
    if to_date:
        events = [e for e in events if _event_date(e.get("timestamp")) <= to_date]

    result = []
    for g in groups:
        gid = g["id"]
        kids = [c for c in children if c.get("groupId") == gid]
        total_balance = sum(c.get("balance", 0) for c in kids)
        period_credited = sum(e.get("credited", 0) for e in events if e.get("childId") in {c["id"] for c in kids})
        result.append({
            "groupId": gid,
            "groupName": g.get("name", gid),
            "childrenCount": len(kids),
            "totalBalance": total_balance,
            "periodCredited": period_credited,
        })
    return result


def get_stats_children(group_id=None, q=None, from_date=None, to_date=None):
    children = get_children()
    groups = get_groups()
    groups_dict = {g["id"]: g.get("name", g["id"]) for g in groups}
    events = get_events()
    if from_date:
        events = [e for e in events if _event_date(e.get("timestamp")) >= from_date]
    if to_date:
        events = [e for e in events if _event_date(e.get("timestamp")) <= to_date]
    if group_id:
        children = [c for c in children if c.get("groupId") == group_id]
    if q:
        ql = q.lower()
        children = [c for c in children if ql in (c.get("fullName") or "").lower()]

    result = []
    for c in children:
        cid = c["id"]
        child_events = [e for e in events if e.get("childId") == cid]
        period_credited = sum(e.get("credited", 0) for e in child_events)
        result.append({
            "id": cid,
            "fullName": c.get("fullName", ""),
            "groupId": c.get("groupId"),
            "groupName": groups_dict.get(c.get("groupId"), c.get("groupId")),
            "balance": c.get("balance", 0),
            "periodCredited": period_credited,
            "actionsCount": len(child_events),
        })
    return result


def adjust_balance(child_id, delta, comment, admin_username):
    child = get_child_by_id(child_id)
    if not child:
        return None
    new_balance = max(0, child["balance"] + delta)
    children = get_children()
    for i, c in enumerate(children):
        if c["id"] == child_id:
            children[i] = {**c, "balance": new_balance}
            break
    _write_json("children", children)
    events = get_events()
    events.append({
        "id": f"adj_{child_id}_{len(events) + 1}",
        "childId": child_id,
        "actionId": "balance_adjust",
        "credited": delta,
        "timestamp": datetime.now().isoformat(),
        "balanceAfter": new_balance,
        "meta": {"comment": comment, "admin": admin_username},
    })
    _write_json("events", events)
    return new_balance


# --- CRUD групп и детей (админ) ---

def create_group(name):
    """Создать группу. Возвращает id или None при ошибке."""
    _ensure_defaults()
    groups = get_groups()
    gid = f"group_{int(datetime.now().timestamp())}"
    groups.append({"id": gid, "name": (name or "").strip() or "Новая группа"})
    _write_json("groups", groups)
    return gid


def update_group(group_id, name):
    """Обновить название группы. Возвращает True/False."""
    _ensure_defaults()
    groups = get_groups()
    for i, g in enumerate(groups):
        if g["id"] == group_id:
            groups[i] = {**g, "name": (name or "").strip() or g.get("name", "")}
            _write_json("groups", groups)
            return True
    return False


def delete_group(group_id):
    """Удалить группу. Возвращает True или строку с ошибкой (если в группе есть дети)."""
    _ensure_defaults()
    children = get_children()
    if any(c.get("groupId") == group_id for c in children):
        return "В группе есть дети. Сначала переместите или удалите их."
    groups = get_groups()
    groups = [g for g in groups if g["id"] != group_id]
    _write_json("groups", groups)
    return True


def create_child(full_name, group_id):
    """Создать ребёнка. group_id может быть пустым. Возвращает id или None."""
    _ensure_defaults()
    groups = get_groups()
    if group_id and not any(g["id"] == group_id for g in groups):
        return None
    children = get_children()
    cid = f"child_{int(datetime.now().timestamp())}"
    children.append({
        "id": cid,
        "fullName": (full_name or "").strip() or "Без имени",
        "groupId": group_id or None,
        "balance": 0,
        "avatar": None,
    })
    _write_json("children", children)
    return cid


def update_child(child_id, full_name, group_id):
    """Обновить ребёнка. group_id может быть None. Возвращает True/False."""
    _ensure_defaults()
    children = get_children()
    for i, c in enumerate(children):
        if c["id"] == child_id:
            children[i] = {
                **c,
                "fullName": (full_name or "").strip() or c.get("fullName", ""),
                "groupId": group_id if group_id else None,
            }
            _write_json("children", children)
            return True
    return False


def delete_child(child_id):
    """Удалить ребёнка и все его события. Возвращает True/False."""
    _ensure_defaults()
    ensure_monthly_reset_done()
    children = _read_json("children")
    orig_len = len(children)
    children = [c for c in children if c["id"] != child_id]
    if len(children) == orig_len:
        return False
    _write_json("children", children)
    events = get_events()
    events = [e for e in events if e.get("childId") != child_id]
    _write_json("events", events)
    return True


def get_monthly_results(group_id=None):
    """Список итогов по месяцам (year, month, children snapshot, totalSum), новые первые.
    Если group_id задан — в каждой записи только дети этой группы и totalSum по группе."""
    _ensure_defaults()
    results = _read_json_any("monthly_results") or []
    results = list(reversed(results))
    if group_id:
        out = []
        for row in results:
            children = [c for c in (row.get("children") or []) if c.get("groupId") == group_id]
            total_sum = sum(c.get("balance", 0) for c in children)
            out.append({**row, "children": children, "totalSum": total_sum})
        return out
    return results


def _month_range(year, month):
    """Возвращает (from_date, to_date) в формате YYYY-MM-DD для данного месяца."""
    from_date = date(year, month, 1).strftime("%Y-%m-%d")
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    to_date = last.strftime("%Y-%m-%d")
    return from_date, to_date


def get_monthly_stats(year, month, group_id=None):
    """Расширенная статистика за один месяц: итоги, по действиям, топы по баллам и по активности.
    Использует снимок из monthly_results для баллов и события за месяц для активности."""
    _ensure_defaults()
    from_date, to_date = _month_range(year, month)
    results = _read_json_any("monthly_results") or []
    row = None
    for r in reversed(results):
        if r.get("year") == year and r.get("month") == month:
            row = r
            break
    children_snapshot = (row.get("children") or []) if row else []
    if group_id:
        children_snapshot = [c for c in children_snapshot if c.get("groupId") == group_id]
    total_coins = sum(c.get("balance", 0) for c in children_snapshot)
    children_count = len(children_snapshot)
    avg_coins = round(total_coins / children_count, 1) if children_count else 0

    events = get_events()
    events = [e for e in events if _event_date(e.get("timestamp")) >= from_date and _event_date(e.get("timestamp")) <= to_date]
    if group_id:
        child_ids_in_group = {c.get("childId") for c in children_snapshot}
        if not child_ids_in_group:
            current_children = get_children()
            child_ids_in_group = {c["id"] for c in current_children if c.get("groupId") == group_id}
        events = [e for e in events if e.get("childId") in child_ids_in_group]

    total_actions = len(events)
    actions_config = get_actions_config()
    actions_dict = {a["id"]: a.get("name", a["id"]) for a in actions_config}
    actions_dict["balance_adjust"] = "Корректировка баланса"

    by_action = {}
    for e in events:
        aid = e.get("actionId") or "?"
        if aid not in by_action:
            by_action[aid] = {"actionId": aid, "actionName": actions_dict.get(aid, aid), "count": 0, "totalCoins": 0}
        by_action[aid]["count"] += 1
        by_action[aid]["totalCoins"] += e.get("credited", 0)
    by_action_list = sorted(by_action.values(), key=lambda x: -x["count"])

    child_actions = {}
    for e in events:
        cid = e.get("childId")
        if cid:
            child_actions[cid] = child_actions.get(cid, 0) + 1
    children_names = {c.get("childId"): c.get("fullName", "") for c in children_snapshot}
    child_to_group = {c.get("childId"): c.get("groupId") for c in children_snapshot}
    groups = get_groups()
    groups_dict = {g["id"]: g.get("name", g["id"]) for g in groups}
    current_children = get_children()
    for c in current_children:
        if c["id"] not in children_names:
            children_names[c["id"]] = c.get("fullName", c["id"])
        if c["id"] not in child_to_group:
            child_to_group[c["id"]] = c.get("groupId")
    top_by_actions = [
        {
            "childId": cid,
            "fullName": children_names.get(cid, cid),
            "actionsCount": cnt,
            "groupName": groups_dict.get(child_to_group.get(cid), ""),
        }
        for cid, cnt in sorted(child_actions.items(), key=lambda x: -x[1])[:15]
    ]

    top_by_coins = sorted(children_snapshot, key=lambda c: -(c.get("balance") or 0))[:15]
    top_by_coins = [
        {
            "childId": c.get("childId"),
            "fullName": c.get("fullName", ""),
            "balance": c.get("balance", 0),
            "groupName": groups_dict.get(c.get("groupId"), ""),
        }
        for c in top_by_coins
    ]

    by_group = {}
    for c in children_snapshot:
        gid = c.get("groupId") or ""
        if gid not in by_group:
            by_group[gid] = {"groupId": gid, "groupName": groups_dict.get(gid, gid), "totalCoins": 0, "childrenCount": 0}
        by_group[gid]["totalCoins"] += c.get("balance", 0)
        by_group[gid]["childrenCount"] += 1
    by_group_list = []
    for g in by_group.values():
        g["avgCoins"] = round(g["totalCoins"] / g["childrenCount"], 1) if g["childrenCount"] else 0
        by_group_list.append(g)
    by_group_list.sort(key=lambda x: -x["totalCoins"])

    return {
        "year": year,
        "month": month,
        "summary": {
            "totalCoins": total_coins,
            "totalActions": total_actions,
            "avgCoinsPerChild": avg_coins,
            "childrenCount": children_count,
        },
        "byAction": by_action_list,
        "topChildrenByCoins": top_by_coins,
        "topChildrenByActions": top_by_actions,
        "byGroup": by_group_list,
    }


# --- Админы (JSON, вместо SQLite auth_user) ---

def get_admins():
    """Список админов из admins.json: [{ username, password_hash, is_staff }, ...]."""
    _ensure_defaults()
    return _read_json_any("admins") or []


def get_admin_by_username(username):
    """Найти админа по username. Возвращает dict или None."""
    if not username:
        return None
    for a in get_admins():
        if (a.get("username") or "").strip() == username.strip():
            return a
    return None


def add_or_update_admin(username, password, is_staff=True, role="admin", group_id=None):
    """Добавить или обновить пользователя в admins.json.
    role: "admin" | "educator". Для educator обязателен group_id."""
    _ensure_defaults()
    username = (username or "").strip()
    if not username:
        return False
    admins = get_admins()
    entry = {"username": username, "password": password or "", "is_staff": bool(is_staff), "role": role or "admin"}
    if group_id:
        entry["group_id"] = group_id
    found = False
    for i, a in enumerate(admins):
        if (a.get("username") or "").strip() == username:
            admins[i] = {**a, **entry}
            found = True
            break
    if not found:
        admins.append(entry)
    _write_json("admins", admins)
    return True
