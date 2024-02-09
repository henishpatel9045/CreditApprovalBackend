from rest_framework.test import APIClient, APITestCase

from core.models import Customer, Loan
from core.loan_test_data import LOAN_TEST_DATA
from core.constants import LOAN_UNSUCCESSFUL_MONTHLY_PAYMENT_EXCEED_50_MESSAGE


# Create your tests here.
class TestCustomer(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.customer_data = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 25,
            "phone_number": "1234567890",
            "monthly_salary": 50000,
        }

    def test_customer_register(self):
        response = self.client.post("/register/", self.customer_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["approved_limit"], 1800000)
        Customer.objects.filter(customer_id=response.data["customer_id"]).delete()


class TestLoan(APITestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        test_suit = [
            "test_loan_eligibility_return_updated_interest_rate",
            "test_loan_eligibility_rejected_exceed_50_salary",
            "test_loan_eligibility_approved_with_updated_interest_rate",
            "test_create_loan_successful",
            "test_create_loan_unsuccessful",
            "test_retrieve_single_loan",
            "test_retrieve_customer_loans",
        ]
        Customer(
            first_name="John",
            last_name="Doe",
            age=25,
            phone_number="1234567890",
            monthly_salary=253000.0,
            approved_limit=3900000.0,
        ).save()
        self.customer = Customer.objects.get(first_name="John")
        for loan in LOAN_TEST_DATA:
            Loan(
                customer=self.customer,
                **loan,
            ).save()

    def test_loan_eligibility_approved_same_interest_rate(self):
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000,
            "interest_rate": 8,
            "tenure": 10,
        }
        response = self.client.post("/check-eligibility", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["corrected_interest_rate"], 8.0)
        self.assertTrue(response.data["approval"])

    def test_loan_eligibility_rejected_exceed_50_salary(self):
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 1000000,
            "interest_rate": 8,
            "tenure": 3,
        }
        response = self.client.post("/check-eligibility", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["corrected_interest_rate"], 8.0)
        self.assertFalse(response.data["approval"])

    def test_loan_eligibility_approved_with_updated_interest_rate(self):
        loans = Loan.objects.all()
        for loan in loans[:4]:
            loan.emis_paid_on_time = 0
            loan.save()
        for loan in loans[4:]:
            loan.emis_paid_on_time = loan.tenure
            loan.save()

        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 100000,
            "interest_rate": 8,
            "tenure": 10,
        }
        response = self.client.post("/check-eligibility", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["corrected_interest_rate"], 16.0)
        self.assertTrue(response.data["approval"])

    def test_create_loan_successful(self):
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 10000,
            "interest_rate": 16,
            "tenure": 10,
        }
        response = self.client.post("/create-loan", data)
        loan = Loan.objects.get(loan_id=response.data["loan_id"])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(loan.customer.customer_id, self.customer.customer_id)
        self.assertEqual(loan.loan_amount, 10000)
        self.assertEqual(loan.interest_rate, 16)
        self.assertEqual(loan.tenure, 10)
        loan.delete()

    def test_create_loan_unsuccessful(self):
        data = {
            "customer_id": self.customer.customer_id,
            "loan_amount": 1000000,
            "interest_rate": 8,
            "tenure": 3,
        }
        response = self.client.post("/create-loan", data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["loan_id"], None)
        self.assertEqual(
            response.data["message"],
            LOAN_UNSUCCESSFUL_MONTHLY_PAYMENT_EXCEED_50_MESSAGE,
        )

    def test_retrieve_single_loan(self):
        loan = Loan.objects.first()
        response = self.client.get(f"/view-loan/{loan.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["loan_id"], loan.loan_id)
        self.assertEqual(
            response.data["customer"].get("customer_id"), loan.customer.customer_id
        )
        self.assertEqual(response.data["loan_amount"], loan.loan_amount)
        self.assertEqual(response.data["interest_rate"], loan.interest_rate)
        self.assertEqual(response.data["tenure"], loan.tenure)
        self.assertEqual(response.data["monthly_installment"], loan.monthly_payment)

    def test_retrieve_customer_loans(self):
        response = self.client.get(f"/view-loans/{self.customer.customer_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            len(response.data), Loan.objects.filter(customer=self.customer).count()
        )
