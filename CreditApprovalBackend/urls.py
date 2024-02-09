from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Credit Approval System API",
        default_version="v1",
        description="API Documentation for Credit Approval System",
        contact=openapi.Contact(email="henishpatel9045@gmail.com"),
    ),
    public=True,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]

urlpatterns += staticfiles_urlpatterns()
