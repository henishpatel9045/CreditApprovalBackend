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
