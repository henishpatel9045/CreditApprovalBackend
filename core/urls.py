from rest_framework.routers import DefaultRouter
from django.urls import path

from core.views import CustomerRegisterViewSet, LoanEligibilityCheckAPIView


router = DefaultRouter()
router.register(r"register", CustomerRegisterViewSet, basename="customer")

urlpatterns = [
    path("check-eligibility", LoanEligibilityCheckAPIView.as_view()),
]
urlpatterns += router.urls
