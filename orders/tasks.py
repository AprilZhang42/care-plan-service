#from celery import shared_task
import logging

from celery import shared_task

from orders.llm import generate_care_plan
from orders.models import CarePlan

logger = logging.getLogger(__name__)

@shared_task
def hello(name):
    print(f"hello, {name}")
    return f"hello, {name}"

@shared_task(bind=True, max_retries=3)
def generate_care_plan_task(self, careplan_id):
    try:
        care_plan = CarePlan.objects.get(id=careplan_id)
    except CarePlan.DoesNotExist:
        logger.warning("care plan %s 不存在，跳过", careplan_id)
        return

    # 1. 开始处理：pending → processing
    care_plan.status = CarePlan.Status.PROCESSING
    care_plan.save()
    logger.info("开始处理 care plan %s", careplan_id)

    # 2. 拼给 LLM 的输入
    order = care_plan.order
    llm_input = {
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
    }

    # 3. 调 LLM；失败就按 1、2、4 秒重试，3 次都失败才标记 failed
    try:
        content = generate_care_plan(llm_input)
    except Exception as exc:
        if self.request.retries < self.max_retries:
            wait = 2 ** self.request.retries
            logger.warning(
                "care plan %s 第 %s 次失败，%s 秒后重试：%s",
                careplan_id, self.request.retries + 1, wait, exc,
            )
            raise self.retry(exc=exc, countdown=wait)

        logger.exception("care plan %s 重试 %s 次后仍然失败", careplan_id, self.max_retries)
        care_plan.status = CarePlan.Status.FAILED
        care_plan.save()
        return

    # 4. 成功：processing → completed
    care_plan.content = content
    care_plan.status = CarePlan.Status.COMPLETED
    care_plan.save()
    logger.info("care plan %s 完成，长度 %s 字", careplan_id, len(content))