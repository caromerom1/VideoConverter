from celery import Celery
import os

celery = Celery("video_tasks", broker=os.environ.get("CELERY_URL", ""))
