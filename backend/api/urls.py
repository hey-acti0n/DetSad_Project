from django.urls import path
from . import views

urlpatterns = [
    path("csrf-set", views.csrf_set),
    path("groups", views.groups_list),
    path("children", views.children_list),
    path("game/actions", views.game_actions),
    path("game/interaction", views.game_interaction),
    path("admin/login", views.admin_login),
    path("admin/logout", views.admin_logout),
    path("admin/me", views.admin_me),
    path("admin/stats/groups", views.admin_stats_groups),
    path("admin/stats/children", views.admin_stats_children),
    path("admin/events", views.admin_events),
    path("admin/monthly-results", views.admin_monthly_results),
    path("admin/child/<str:id>/events", views.admin_child_events),
    path("admin/child/<str:id>/balance-adjust", views.admin_balance_adjust),
    path("admin/groups", views.admin_groups_list),
    path("admin/group/create", views.admin_group_create),
    path("admin/group/<str:id>", views.admin_group_detail),
    path("admin/children/create", views.admin_child_create),
    path("admin/child/<str:id>/update", views.admin_child_update),
    path("admin/child/<str:id>/delete", views.admin_child_delete),
]
