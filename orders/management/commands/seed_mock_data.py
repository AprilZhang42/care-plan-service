from django.core.management.base import BaseCommand

from orders.models import CarePlan, Order, Patient, Provider


class Command(BaseCommand):
    help = "Wipe and repopulate the database with mock patients, providers, orders, and care plans."

    def handle(self, *args, **options):
        CarePlan.objects.all().delete()
        Order.objects.all().delete()
        Patient.objects.all().delete()
        Provider.objects.all().delete()

        dr_lee = Provider.objects.create(name="Dr. Lee", npi="1234567890")
        dr_smith = Provider.objects.create(name="Dr. Smith", npi="9876543210")

        patient_a = Patient.objects.create(first_name="Jane", last_name="Doe", mrn="000123")
        patient_b = Patient.objects.create(first_name="John", last_name="Zhang", mrn="000456")

        # Same patient, two different medications on two different orders —
        # this is the normalization example from Day 3 (patient info stored
        # once, each order just points at it via a foreign key).
        order_1 = Order.objects.create(
            patient=patient_a,
            provider=dr_lee,
            medication_name="IVIG",
            primary_diagnosis="G70.00",
            additional_diagnoses=["I10", "K21.9"],
            medication_history=["Pyridostigmine 60mg PO q6h PRN", "Prednisone 10mg PO daily"],
            patient_records="Progressive proximal muscle weakness and ptosis over 2 weeks.",
        )
        CarePlan.objects.create(
            order=order_1,
            content=(
                "Problem list: Need for rapid immunomodulation.\n"
                "Goals: Clinically meaningful improvement in 2 weeks.\n"
                "Interventions: IVIG dosing, premedication, infusion monitoring.\n"
                "Monitoring: CBC/BMP before infusion, vitals during, renal function after."
            ),
            status=CarePlan.Status.COMPLETED,
        )

        order_2 = Order.objects.create(
            patient=patient_a,
            provider=dr_lee,
            medication_name="Prednisone",
            primary_diagnosis="G70.00",
            additional_diagnoses=["I10"],
            medication_history=["Pyridostigmine 60mg PO q6h PRN"],
            patient_records="Follow-up visit, tapering steroid dose.",
        )
        CarePlan.objects.create(order=order_2, status=CarePlan.Status.PENDING)

        order_3 = Order.objects.create(
            patient=patient_b,
            provider=dr_smith,
            medication_name="Metformin",
            primary_diagnosis="E11.9",
            additional_diagnoses=[],
            medication_history=["Lisinopril 10mg PO daily"],
            patient_records="Newly diagnosed type 2 diabetes.",
        )
        CarePlan.objects.create(order=order_3, status=CarePlan.Status.PROCESSING)

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Provider.objects.count()} providers, "
                f"{Patient.objects.count()} patients, "
                f"{Order.objects.count()} orders, "
                f"{CarePlan.objects.count()} care plans."
            )
        )
