from rest_framework.routers import SimpleRouter

from .views import StoreViewSet


router = SimpleRouter()
router.register(r"stores", StoreViewSet, basename="store")
urlpatterns = router.urls
