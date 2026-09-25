import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .llm import generate_care_plan

# MVP storage: everything lives in this dict while the process is running.
# Restarting the server wipes it. A real database comes later.
ORDERS = {}
_next_id = 1


def index(request):
    return render(request, "orders/index.html")


@csrf_exempt
@require_http_methods(["POST"])
def create_order(request):
    global _next_id

    data = json.loads(request.body)

    order = {
        "id": _next_id,
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "referring_provider": data.get("referring_provider"),
        "referring_provider_npi": data.get("referring_provider_npi"),
        "mrn": data.get("mrn"),
        "primary_diagnosis": data.get("primary_diagnosis"),
        "medication_name": data.get("medication_name"),
        "additional_diagnoses": data.get("additional_diagnoses"),
        "medication_history": data.get("medication_history"),
        "patient_records": data.get("patient_records"),
    }

    order["care_plan"] = generate_care_plan(order)

    ORDERS[_next_id] = order
    _next_id += 1

    return JsonResponse(order)
