import logging
import os

from anthropic import Anthropic

logger = logging.getLogger(__name__)
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
    #raise RuntimeError("测试重试：故意失败")    
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
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    logger.info("stop_reason=%s, blocks=%s", response.stop_reason, [b.type for b in response.content])
    if response.stop_reason == "max_tokens":
        raise RuntimeError("LLM 输出被截断，max_tokens 不够")
    for block in response.content:
        if block.type == "text":
            return block.text
    raise RuntimeError(f"LLM 没有返回文字内容，stop_reason={response.stop_reason}")
    #return ""
