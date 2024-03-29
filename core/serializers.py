import datetime
from rest_framework import serializers

from core.models import Customer, Loan
from core.utils import calculate_emis_till_date


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "customer_id",
            "first_name",
            "last_name",
            "age",
            "phone_number",
            "monthly_salary",
            "approved_limit",
        )
        read_only_fields = ("customer_id", "approved_limit")

    def calculate_approved_limit(self, monthly_salary: int) -> int:
        """Calculate the approved limit based on the monthly salary"""
        return round((36 * monthly_salary) / 100_000) * 100_000

    def create(self, validated_data):
        validated_data["approved_limit"] = self.calculate_approved_limit(
            validated_data["monthly_salary"]
        )
        return super().create(validated_data)


class LoanRequestBodySerializer(serializers.Serializer):
    """
    Serializer for the request body of creating and checking eligibility of a loan.
    """

    customer_id = serializers.IntegerField()
    loan_amount = serializers.FloatField()
    interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()


class LoanEligibilityResponseSerializer(serializers.Serializer):
    """
    Serializer for the response of the loan eligibility check API.
    """

    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.FloatField()
    corrected_interest_rate = serializers.FloatField()
    tenure = serializers.IntegerField()
    monthly_installment = serializers.FloatField()


class LoanCreateResponseSerializer(serializers.Serializer):
    """
    Serializer for the response of the create loan API.
    """

    loan_id = serializers.IntegerField(allow_null=True)
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.FloatField()


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = "__all__"

    def to_representation(self, instance):
        "if extra attribute passed while creting this serializer like create_view then use LoanCreateResponseSerializer"
        data = LoanCreateResponseSerializer(
            data={
                "loan_id": instance.loan_id,
                "customer_id": instance.customer.customer_id,
                "loan_approved": True if instance.loan_id else False,
                "monthly_installment": instance.monthly_payment,
                "message": self.context.get("message"),
            }
        )
        data.is_valid(raise_exception=True)
        return data.data


class CustomerRetrieveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = (
            "customer_id",
            "first_name",
            "last_name",
            "age",
            "phone_number",
        )


class LoanSingleRecordSerializer(serializers.ModelSerializer):
    customer = CustomerRetrieveSerializer()
    monthly_installment = serializers.FloatField(source="monthly_payment")

    class Meta:
        model = Loan
        fields = (
            "loan_id",
            "customer",
            "loan_amount",
            "interest_rate",
            "tenure",
            "monthly_installment",
        )


class CustomerLoanSerializer(serializers.ModelSerializer):
    monthly_installment = serializers.FloatField(source="monthly_payment")
    repayments_left = serializers.SerializerMethodField()

    def get_repayments_left(self, obj: Loan) -> int:
        emis_till_date = calculate_emis_till_date(
            obj.tenure, obj.emis_paid_on_time, obj.date_of_approval, obj.end_date
        )
        return obj.tenure - emis_till_date

    class Meta:
        model = Loan
        fields = (
            "loan_id",
            "loan_amount",
            "interest_rate",
            "monthly_installment",
            "repayments_left",
        )
