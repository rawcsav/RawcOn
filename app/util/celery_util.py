from celery import Celery
from flask import Flask

celery = Celery(__name__)


def make_celery(app: Flask):
    celery.conf.broker_url = app.config["CELERY_BROKER_URL"]
    celery.conf.result_backend = app.config["CELERY_RESULT_BACKEND"]
    celery.conf.imports = app.config["CELERY_IMPORTS"]
    celery.conf.beat_schedule = app.config["CELERY_BEAT_SCHEDULE"]
    celery.broker_connection_retry_on_startup = True

    TaskBase = celery.Task

    class ContextTask(TaskBase):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    celery.finalize()
    return celery
