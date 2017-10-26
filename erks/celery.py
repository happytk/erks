from flask_celeryext import create_celery_app
# from flask_appfactory.celery import celeryfactory
from ercc import create_app

# celery = celeryfactory(create_app())
celery = create_celery_app(create_app())
