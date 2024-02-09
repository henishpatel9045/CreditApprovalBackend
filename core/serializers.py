from rest_framework import serializers

from core.models import Customer, Loan


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
