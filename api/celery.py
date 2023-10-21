from celery import Celery
import os

celery = Celery("tasks", broker=os.environ.get("CELERY_URL", ""))
