from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/finance/", include("apps.finance.api.urls")),
    path("api/v1/mensageria/", include("apps.provider_mensageria.api.urls")),
]
