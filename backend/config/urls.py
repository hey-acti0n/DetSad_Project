from django.urls import path, include, re_path
from django.views.static import serve
from django.conf import settings

urlpatterns = [
    path("api/v1/", include("api.urls")),
    re_path(r"^.*$", lambda req: serve(req, "index.html", document_root=settings.STATIC_ROOT)),
]
