from celery import Celery
from app.config import settings

# Cria a instância da aplicação Celery
celery_app = Celery(
    "tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks"] # Aponta para o nosso ficheiro de tarefas
)

celery_app.conf.update(
    task_track_started=True,
)
