from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from core.models import Customer
from core.serializers import (
    CustomerSerializer,
    LoanRequestBodySerializer,
    LoanEligibilityResponseSerializer,
)
from core.utils import determine_loan_eligibility
from core.decorators import handle_exceptions


class CustomerRegisterViewSet(CreateModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class LoanEligibilityCheckAPIView(APIView):
    @handle_exceptions
    def post(self, request: Request) -> Response:
        data = LoanRequestBodySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        data = data.validated_data
        customer = Customer.objects.get(customer_id=data["customer_id"])
        is_eligible, _, updated_data = determine_loan_eligibility(
            data["loan_amount"], data["interest_rate"], data["tenure"], customer
        )
        res_data = LoanEligibilityResponseSerializer(
            data={
                "customer_id": customer.customer_id,
                "approval": is_eligible,
                "interest_rate": data["interest_rate"],
                "corrected_interest_rate": updated_data.get("interest_rate"),
                "tenure": data["tenure"],
                "monthly_installment": updated_data.get("monthly_payment"),
            }
        )
        res_data.is_valid(raise_exception=True)

        return Response(
            res_data.data,
            status=status.HTTP_200_OK,
        )
