from django.contrib.postgres.fields import ArrayField
from django.db import models


class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mrn = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (MRN {self.mrn})"


class Provider(models.Model):
    name = models.CharField(max_length=200)
    npi = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.name} (NPI {self.npi})"


class Order(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="orders")
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name="orders")
    medication_name = models.CharField(max_length=200)
    primary_diagnosis = models.CharField(max_length=20)
    additional_diagnoses = ArrayField(models.CharField(max_length=20), default=list, blank=True)
    medication_history = ArrayField(models.CharField(max_length=200), default=list, blank=True)
    patient_records = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id}: {self.medication_name} for {self.patient}"


class CarePlan(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        PROCESSING = "processing"
        COMPLETED = "completed"
        FAILED = "failed"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="care_plan")
    content = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"CarePlan for Order {self.order_id} ({self.status})"
