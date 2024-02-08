from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
import pandas as pd

from core.models import Customer, Loan

CONFIG = [
    {
        "file_path": "core/data/customer_data.xlsx",
        "model": Customer,
        "mapping": {
            "first_name": "First Name",
            "last_name": "Last Name",
            "age": "Age",
            "phone_number": "Phone Number",
            "monthly_salary": "Monthly Salary",
            "approved_limit": "Approved Limit",
        },
    },
    {
        "file_path": "core/data/loan_data.xlsx",
        "model": Loan,
        "mapping": {
            "customer_id": "Customer ID",
            "loan_amount": "Loan Amount",
            "tenure": "Tenure",
            "interest_rate": "Interest Rate",
            "monthly_payment": "Monthly payment",
            "emis_paid_on_time": "EMIs paid on Time",
            "date_of_approval": "Date of Approval",
            "end_date": "End Date",
        },
    },
]


class Command(BaseCommand):
    help = "Load initial data from excel file into database."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--load_initial",
            type=bool,
            help="Set to false when not loading initial data from excel file.",
            default=True,
            required=False,
        )

    def handle(self, *args, **options):
        if Customer.objects.all().count() != 0 or Loan.objects.all().count() != 0:
            self.stdout.write(self.style.ERROR("Data already exists in database."))
            return
        self.stdout.write(
            self.style.SUCCESS("Loading initial data from excel file....")
        )
        try:
            for model_config in CONFIG:
                with transaction.atomic():
                    df = pd.read_excel(model_config["file_path"])
                    print(df.head())
                    for index, row in df.iterrows():
                        obj = model_config.get("model")()
                        for key, value in model_config["mapping"].items():
                            setattr(obj, key, row[value])
                        obj.save()
                        self.stdout.write(
                            self.style.SUCCESS(f"{obj} created successfully.")
                        )

            self.stdout.write(
                self.style.SUCCESS("Data loaded successfully from excel file....")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error occurred: {e}"))
            self.stdout.write(self.style.ERROR("Data not loaded from excel file...."))
            return
