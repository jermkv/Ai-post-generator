from celery import Celery

from app.config import settings

celery_app = Celery(
    'aibot',
    broker=settings.rabbit_url,
    backend=settings.redis_url,
    include=[
        'app.tasks.parsing',
        'app.tasks.pipeline',
        'app.tasks.generation',
        'app.tasks.publishing',
    ]

)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    timezone='UTC',
    enable_utc=True
)

celery_app.conf.beat_schedule = {
    'parse-all-sources': {
        'task': 'tasks.parse_all_sources',
        'schedule': settings.parse_interval_minutes * 60
    },
    # Оркестратор будет проверять новые новости каждые 15 минут
    'run-pipeline-orchestrator': {
        'task': 'tasks.run_pipeline',
        'schedule': settings.generate_interval_minutes * 60
    },
}
