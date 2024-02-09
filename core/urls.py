from rest_framework.routers import DefaultRouter
from django.urls import path

from core.views import (
    CustomerRegisterViewSet,
    LoanEligibilityCheckAPIView,
    CreateLoanAPIView,
    LoanRetrieveViewSet,
    CustomerLoansAPIView,
)


router = DefaultRouter()
router.register(r"register", CustomerRegisterViewSet, basename="customer")
router.register(r"view-loan", LoanRetrieveViewSet, basename="loan")

urlpatterns = [
    path("check-eligibility", LoanEligibilityCheckAPIView.as_view()),
    path("create-loan", CreateLoanAPIView.as_view()),
    path("view-loans/<int:customer_id>", CustomerLoansAPIView.as_view()),
]
urlpatterns += router.urls
