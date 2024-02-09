from rest_framework.routers import DefaultRouter

from core.views import CustomerRegisterViewSet


router = DefaultRouter()
router.register(r"register", CustomerRegisterViewSet, basename="customer")

urlpatterns = router.urls