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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework import permissions, response, reverse, schemas
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


spectacular_urlpatterns = [
    # ... your other URLs ...
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]


auth_urls = [
    path("", include("rest_framework.urls")),
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

urls = [
    path("", include("cart.urls")),
    path("", include("customers.urls")),
    path("", include("discount.urls")),
    path("", include("orders.urls")),
    path("", include("payments.urls")),
    path("", include("catalogue.urls")),
    path("", include("stores.urls")),
    path("", include("wishlist.urls")),
    path(
        "openapi/",
        schemas.get_schema_view(
            title="e-commerce API", description="e-commerce API Schema", version="1.0"
        ),
        name="openapi-schema",
    ),
]


urlpatterns = [
    path("__debug__/", include("debug_toolbar.urls")),
    path("admin/", admin.site.urls),
    path("auth/", include(auth_urls)),
    path("api/v1/", include(urls)),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += spectacular_urlpatterns
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


class APIRoot(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, format=None):
        return response.Response(
            {
                "catalogue": reverse.reverse("products", request=request, format=format),
                "stores": reverse.reverse("store-list", request=request, format=format),
                "cart": reverse.reverse("cart", request=request, format=format),
                "wishlists": reverse.reverse("wishlists", request=request, format=format),
                "orders": reverse.reverse("orders", request=request, format=format),
                "offers": reverse.reverse("offers", request=request, format=format),
            }
        )


urlpatterns.append(path("", APIRoot.as_view()))
