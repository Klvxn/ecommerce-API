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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg.views import get_schema_view
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import permissions, response, reverse, schemas
from rest_framework.views import APIView
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

auth_urls = [
    path("", include("rest_framework.urls")),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urls = [
    path("", include("cart.urls")),
    path("", include("customers.urls")),
    path("", include("orders.urls")),
    path("", include("payments.urls")),
    path("", include("products.urls")),
    path("", include("vendors.urls")),
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


urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path("auth/", include(auth_urls)),
    path("api/v1/", include(urls)),
    path("", include(swagger_urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


class APIRoot(APIView):

    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(operation_summary="API Root", tags=["/"])
    def get(self, request, format=None):
        return response.Response({
            "products": reverse.reverse("products", request=request, format=format),
            "discounts": reverse.reverse("discounts", request=request, format=format),
            "vendors": reverse.reverse("vendor-list", request=request, format=format),
            "cart": reverse.reverse("cart", request=request, format=format),
        })


urlpatterns.append(path("", APIRoot.as_view()))