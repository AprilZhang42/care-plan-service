import logging
import time
import redis
from django.core.management.base import BaseCommand

from orders.models import CarePlan
from orders.llm import generate_care_plan

logger = logging.getLogger(__name__)
redis_client = redis.Redis(host="redis", port=6379, socket_timeout=10)


class Command(BaseCommand):
    help = "手写版 worker：从 Redis 队列取 care plan id，调用 LLM 生成内容"

    def handle(self, *args, **options):
        self.stdout.write("worker 已启动，等待任务...")
        while True:
            #result = redis_client.brpop("careplan_queue", timeout=5)
            try:
                result = redis_client.brpop("careplan_queue", timeout=5)
            except redis.exceptions.RedisError:
                logger.warning("连接 Redis 出错，1 秒后重试", exc_info=True)
                time.sleep(1)
                continue
            if result is None:
                continue                      # 5 秒内没任务，回去继续等
            _, raw_id = result                # result 是 (队列名, id)，只要 id
            self.process(int(raw_id))

    def process(self, careplan_id):
        try:
            care_plan = CarePlan.objects.get(id=careplan_id)
        except CarePlan.DoesNotExist:
            logger.warning("care plan %s 不存在，跳过", careplan_id)
            return

        # 1. 开始处理：pending → processing
        care_plan.status = CarePlan.Status.PROCESSING
        care_plan.save()
        logger.info("开始处理 care plan %s", careplan_id)

        # 2. 去数据库拿完整信息，拼成给 LLM 的输入
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

        # 3. 调 LLM；出错就标记 failed（手写版先不做重试）
        try:
            content = generate_care_plan(llm_input)
        except Exception:
            logger.exception("care plan %s 生成失败", careplan_id)
            care_plan.status = CarePlan.Status.FAILED
            care_plan.save()
            return

        # 4. 成功：存内容，processing → completed
        care_plan.content = content
        care_plan.status = CarePlan.Status.COMPLETED
        care_plan.save()
        logger.info("care plan %s 完成，长度 %s 字", careplan_id, len(content))