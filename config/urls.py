"""config URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions, schemas
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


schema_view = get_schema_view(
    openapi.Info(
        title="e-commerce API",
        default_version="v1",
        description="Documentation for e-commerce API with payment gateway integration",
        contact=openapi.Contact(email="akpulukelvin@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urls = [
    path("api-auth/", include("rest_framework.urls")),
    path("api-auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api-auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include("cart.urls")),
    path("", include("customers.urls")),
    path("", include("orders.urls")),
    path("", include("payments.urls")),
    path("", include("products.urls")),
    path(
        "openapi/",
        schemas.get_schema_view(
            title="e-commerce API", description="e-commerce API Schema", version="1.0"
        ),
        name="openapi-schema",
    ),
]

swagger_urls = [
    re_path(
        r"^swagger(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^swagger/$",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]

urls += swagger_urls

urlpatterns = [path("admin/", admin.site.urls), path("api/v1/", include(urls))]
