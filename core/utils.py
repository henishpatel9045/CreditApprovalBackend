from datetime import datetime, timedelta
from django.db.models import Count, Sum, When, Case, F, Expression, fields, Value, Q

from core.models import Customer, Loan
from core.constants import (
    LOAN_SUCCESSFUL_MESSAGE,
    LOAN_UNSUCCESSFUL_12_MESSAGE,
    LOAN_UNSUCCESSFUL_16_MESSAGE,
    LOAN_UNSUCCESSFUL_MESSAGE,
    LOAN_UNSUCCESSFUL_MONTHLY_PAYMENT_EXCEED_50_MESSAGE,
)


def calculate_emis_till_date(
    tenure: int,
    emis_paid_on_time: int,
    approval_date: datetime.date,
    end_date: datetime.date,
) -> int:
    """Calculate the total number of actual EMIs till date from the date of approval of loan"""
    today = datetime.today().date()
    if today > end_date or emis_paid_on_time == tenure:
        return tenure
    total_emis = (
        (today.year - approval_date.year) * 12 + today.month - approval_date.month
    )
    return total_emis


def calculate_credit_score(customer: Customer) -> tuple[int, dict]:
    """Calculate the credit score of a customer based on the number of loans and EMIs paid on time

    ## Algorithm:
    - If customer has no loan credit score is 100
    - Credit score will be 0 < score <= 100
    - Check sum of all loans if >= approved_limit then score = 0
    - Credit score wil be based on two parts
        - 80% depends on total loan volume and weight factor (30)
        for normalization and ratio of emi_paid_on_time to total_emis till date.
        - 20% depends on loans taken in last year and weight factor (10)
        for normalization.
    """
    active_loan_predicate = Q(end_date__gte=datetime.today().date()) & Q(
        tenure__gt=F("emis_paid_on_time")
    )
    loans = Loan.objects.filter(customer=customer).aggregate(
        total_amount=Sum(
            Case(
                When(
                    active_loan_predicate,
                    then=F("loan_amount"),
                ),
                default=0,
            )
        ),
        active_loan=Sum(
            Case(
                When(
                    active_loan_predicate,
                    then=1,
                ),
                default=0,
            )
        ),
        total_monthly_payment=Sum(
            Case(
                When(
                    active_loan_predicate,
                    then=F("monthly_payment"),
                ),
                default=0.0,
            )
        ),
        total_loan=Count("loan_id"),
        last_year_loan=Sum(
            Case(
                When(
                    date_of_approval__gte=datetime.today().date() - timedelta(days=365),
                    then=1,
                ),
                default=0,
            )
        ),
        emi_paid=Sum("emis_paid_on_time"),
    )
    approved_loan_date = Loan.objects.filter(customer=customer).values_list(
        "tenure", "emis_paid_on_time", "date_of_approval", "end_date"
    )
    total_emi = 0
    for date in approved_loan_date:
        total_emi += calculate_emis_till_date(*date)
    loans["total_emi"] = total_emi
    for key in loans:
        if not loans[key]:
            loans[key] = 0

    if customer.approved_limit <= loans.get("total_amount", 0):
        return 0, loans
    emis_paid_on_time_factor = loans.get("emi_paid", 0) / (loans.get("total_emi") or 1)
    all_loans = loans.get("total_loan", 0) * 30
    last_year_loan = loans.get("last_year_loan", 0) * 10
    credit_score = min(20, last_year_loan) + min(
        80, min(80, all_loans) * emis_paid_on_time_factor
    )
    return round(credit_score), loans


def calculate_emi(
    loan_amount: float, tenure_months: int, interest_rate: float
) -> float:
    r = (interest_rate / 12) / 100  # Monthly interest rate
    numerator = loan_amount * r * ((1 + r) ** tenure_months)
    denominator = ((1 + r) ** tenure_months) - 1
    emi = numerator / denominator
    return round(emi, 2)


def determine_loan_eligibility(
    loan_amount: float, interest_rate: float, tenure: int, customer: Customer
) -> tuple[bool, bool, dict, str]:
    """Determine the loan eligibility of a customer based on the credit score and monthly payment

    Returns:
    - A tuple of two boolean values and a dictionary (is_eligible, is_interest_rate_updated, loan_data, message)
        - is_eligible: `True` if the customer is eligible for the loan, `False` otherwise
        - is_interest_rate_updated: `True` if the interest rate is updated, `False` otherwise
        - loan_data:
            - monthly_payment: The monthly payment for the loan
            - interest_rate: The updated interest rate for the loan
        - message: A string containing the message for the customer

    """
    credit_score, loan_data = calculate_credit_score(customer)

    monthly_payment = calculate_emi(loan_amount, tenure, interest_rate)
    res_data = {
        "monthly_payment": monthly_payment,
        "interest_rate": interest_rate,
    }
    msg = LOAN_SUCCESSFUL_MESSAGE

    if (
        loan_data["total_monthly_payment"] + monthly_payment
        > customer.monthly_salary * 0.5
    ):
        msg = LOAN_UNSUCCESSFUL_MONTHLY_PAYMENT_EXCEED_50_MESSAGE
        return False, False, res_data, msg

    if credit_score > 50:
        return True, False, res_data, msg

    if credit_score > 30:
        if interest_rate >= 12:
            return True, False, res_data, msg
        res_data["interest_rate"] = 12
        res_data["monthly_payment"] = calculate_emi(loan_amount, tenure, 12)
        msg = LOAN_UNSUCCESSFUL_12_MESSAGE
        return True, True, res_data, msg

    if credit_score > 10:
        if interest_rate >= 16:
            return True, False, res_data, msg
        res_data["interest_rate"] = 16
        res_data["monthly_payment"] = calculate_emi(loan_amount, tenure, 16)
        msg = LOAN_UNSUCCESSFUL_16_MESSAGE
        return True, True, res_data, msg

    return False, False, res_data, LOAN_UNSUCCESSFUL_MESSAGE
