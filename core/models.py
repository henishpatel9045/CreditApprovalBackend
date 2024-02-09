from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=10)
    monthly_salary = models.FloatField()
    approved_limit = models.IntegerField()

    def __str__(self):
        return self.first_name + " " + self.last_name

class Loan(models.Model):
    loan_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    loan_amount = models.IntegerField(default=0)
    tenure = models.IntegerField(default=0)
    interest_rate = models.FloatField(default=0.0)
    monthly_payment = models.FloatField(default=0)
    emis_paid_on_time = models.IntegerField(default=0)
    date_of_approval = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return self.customer.first_name + " " + self.customer.last_name + " " + str(self.loan_id)
