import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .llm import generate_care_plan
from .models import CarePlan, Order, Patient, Provider

logger = logging.getLogger(__name__)


def index(request):
    return render(request, "orders/index.html")


def _parse_list(value):
    if isinstance(value, list):
        return value
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _serialize_order(order, care_plan):
    return {
        "id": order.id,
        "first_name": order.patient.first_name,
        "last_name": order.patient.last_name,
        "mrn": order.patient.mrn,
        "referring_provider": order.provider.name,
        "referring_provider_npi": order.provider.npi,
        "primary_diagnosis": order.primary_diagnosis,
        "additional_diagnoses": order.additional_diagnoses,
        "medication_name": order.medication_name,
        "medication_history": order.medication_history,
        "patient_records": order.patient_records,
        "care_plan": care_plan.content,
        "status": care_plan.status,
    }


@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    data = json.loads(request.body)

    patient, _ = Patient.objects.get_or_create(
        mrn=data.get("mrn"),
        defaults={
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name"),
        },
    )

    provider, _ = Provider.objects.get_or_create(
        npi=data.get("referring_provider_npi"),
        defaults={"name": data.get("referring_provider")},
    )

    order = Order.objects.create(
        patient=patient,
        provider=provider,
        medication_name=data.get("medication_name"),
        primary_diagnosis=data.get("primary_diagnosis"),
        additional_diagnoses=_parse_list(data.get("additional_diagnoses")),
        medication_history=_parse_list(data.get("medication_history")),
        patient_records=data.get("patient_records") or "",
    )

    logger.info("received request, created order %s", order.id)

    llm_input = {
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "mrn": patient.mrn,
        "referring_provider": provider.name,
        "referring_provider_npi": provider.npi,
        "primary_diagnosis": order.primary_diagnosis,
        "additional_diagnoses": order.additional_diagnoses,
        "medication_name": order.medication_name,
        "medication_history": order.medication_history,
        "patient_records": order.patient_records,
    }

    logger.info("calling LLM for order %s (%s)", order.id, order.medication_name)
    content = generate_care_plan(llm_input)
    logger.info("LLM returned, care_plan length=%s chars", len(content))

    care_plan = CarePlan.objects.create(
        order=order,
        content=content,
        status=CarePlan.Status.COMPLETED,
    )

    return JsonResponse(_serialize_order(order, care_plan))


def get_order(request, order_id):
    try:
        order = Order.objects.select_related("patient", "provider", "care_plan").get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({"error": "Order not found"}, status=404)

    return JsonResponse(_serialize_order(order, order.care_plan))
