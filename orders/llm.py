import os

from anthropic import Anthropic

_client = None


def _get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
        _client = Anthropic(api_key=api_key)
    return _client


def generate_care_plan(order):
    prompt = f"""You are a clinical pharmacist writing a care plan for a specialty pharmacy order.

Patient: {order['first_name']} {order['last_name']} (MRN: {order['mrn']})
Referring Provider: {order['referring_provider']} (NPI: {order['referring_provider_npi']})
Primary Diagnosis (ICD-10): {order['primary_diagnosis']}
Additional Diagnoses: {order['additional_diagnoses']}
Medication: {order['medication_name']}
Medication History: {order['medication_history']}
Patient Records: {order['patient_records']}

Write a care plan with exactly these sections:
1. Problem list / Drug therapy problems (DTPs)
2. Goals (SMART)
3. Pharmacist interventions / plan
4. Monitoring plan & lab schedule
"""

    client = _get_client()
    response = client.messages.create(
        model=os.environ.get("LLM_MODEL", "claude-sonnet-5"),
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
