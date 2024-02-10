import calendar
import datetime
from dateutil import relativedelta
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema

from core.models import Customer, Loan
from core.serializers import (
    CustomerSerializer,
    LoanRequestBodySerializer,
    LoanEligibilityResponseSerializer,
    LoanSerializer,
    LoanCreateResponseSerializer,
    LoanSingleRecordSerializer,
    CustomerLoanSerializer,
)
from core.utils import determine_loan_eligibility
from core.decorators import handle_exceptions


class CustomerRegisterViewSet(CreateModelMixin, GenericViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    @swagger_auto_schema(
        tags=["Customer"],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class LoanEligibilityCheckAPIView(APIView):
    @swagger_auto_schema(
        tags=["Loan"],
        operation_description=(
            "Check if the customer is eligible for the loan. \
            If the customer is not eligible, the API will return the \
            corrected interest rate and the monthly installment if possible. \
            If the customer is eligible, the API will return the\
            interest rate and the monthly installment."
        ),
        request_body=LoanRequestBodySerializer,
        responses={200: LoanEligibilityResponseSerializer},
    )
    @handle_exceptions
    def post(self, request: Request) -> Response:
        data = LoanRequestBodySerializer(data=request.data)
        data.is_valid(raise_exception=True)
        data = data.validated_data
        customer = Customer.objects.get(customer_id=data["customer_id"])
        is_eligible, _, updated_data, _ = determine_loan_eligibility(
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


class CreateLoanAPIView(APIView):
    def calculate_end_date(
        self, start_date: datetime.date, tenure: int
    ) -> datetime.date:
        end_date = start_date + relativedelta.relativedelta(months=tenure)
        end_of_month = calendar.monthrange(end_date.year, end_date.month)[1]
        if end_date.day > end_of_month:
            end_date = end_date.replace(day=end_of_month)
        return end_date

    @swagger_auto_schema(
        tags=["Loan"],
        operation_description=(
            "Create a loan for the customer. \
            If the customer is not eligible, the loan will not be approved. \
            If the customer is eligible, the loan will be approved."
        ),
        request_body=LoanRequestBodySerializer,
        responses={200: LoanCreateResponseSerializer},
    )
    @handle_exceptions
    def post(self, request: Request) -> Response:
        req_data = LoanRequestBodySerializer(data=request.data)
        req_data.is_valid(raise_exception=True)
        req_data = req_data.validated_data
        customer = Customer.objects.get(customer_id=req_data["customer_id"])
        is_eligible, is_updated, updated_data, message = determine_loan_eligibility(
            req_data["loan_amount"],
            req_data["interest_rate"],
            req_data["tenure"],
            customer,
        )

        data = {
            "customer": customer.customer_id,
            "loan_amount": req_data["loan_amount"],
            "interest_rate": updated_data.get("interest_rate"),
            "tenure": req_data["tenure"],
            "monthly_payment": int(updated_data.get("monthly_payment")),
        }

        # If the customer is not eligible or the interest rate is updated, then the loan is not approved
        if not is_eligible or is_updated:
            data = {
                "loan_id": None,
                "customer_id": customer.customer_id,
                "loan_approved": False,
                "monthly_payment": updated_data.get("monthly_payment"),
                "message": message,
            }
            return Response(
                data,
                status=status.HTTP_200_OK,
            )

        # Add the date of approval and end date
        today = datetime.date.today()
        data["date_of_approval"] = today
        data["end_date"] = self.calculate_end_date(today, req_data["tenure"])

        # Save the loan
        serializer = LoanSerializer(data=data, context={"message": message})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class LoanRetrieveViewSet(RetrieveModelMixin, GenericViewSet):
    queryset = Loan.objects.all().prefetch_related("customer")
    serializer_class = LoanSingleRecordSerializer

    @swagger_auto_schema(
        tags=["Loan"],
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class CustomerLoansAPIView(APIView):
    @swagger_auto_schema(
        tags=["Customer"],
        operation_description="Retrieve all the loans of a customer",
        responses={200: CustomerLoanSerializer(many=True)},
    )
    @handle_exceptions
    def get(self, request: Request, customer_id: int) -> Response:
        loans = Loan.objects.filter(customer_id=customer_id)
        data = CustomerLoanSerializer(loans, many=True)
        return Response(
            data.data,
            status=status.HTTP_200_OK,
        )
