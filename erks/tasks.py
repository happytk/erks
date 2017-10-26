# from manage import app, celery
# from . import create_app
from celery import shared_task
from flask_celeryext import RequestContextTask
# from . import celery  # make_celery
from flask import current_app
# _app = create_app(register_blueprints=False)
# _celery = make_celery(_app)
# from celery.schedules import crontab
# from datetime import timedelta


@shared_task(base=RequestContextTask)
def worker_beat():
    from erks.models import SiteConfiguration
    from erks.models import SchemaCollector

    # for-alive-check
    SiteConfiguration.objects.only('id').first().update_worker_indicator()

    # schema-collector
    SchemaCollector.run()



@shared_task(base=RequestContextTask)
def _sendmail(receiver, title, body):
    from erks.utils.email import sendmail as sendmail_direct
    sendmail_direct(receiver, title, body)


def sendmail(receiver, title, body):
    app = current_app._get_current_object()
    if app.config['MAIL_SENT_ASYNC']:
        _sendmail.delay(receiver, title, body)
    else:
        _sendmail(receiver, title, body)


@shared_task(base=RequestContextTask)
def _build_glossary_report(report_id):
    from erks.models import GlossaryReport
    report = GlossaryReport.objects.get(id=report_id)
    report.inspect()


@shared_task(base=RequestContextTask)
def _xls_loader(loader_id):
    from erks.models import XlsLoaderHistory
    loader = XlsLoaderHistory.objects.get(id=loader_id)
    loader.run()


@shared_task(base=RequestContextTask)
def _build_glossary_model_report(report_id):
    from erks.models import GlossaryModelReport
    report = GlossaryModelReport.objects.get(id=report_id)
    report.inspect()


@shared_task(base=RequestContextTask)
def _collect_schema(project_id, schema_collector_id):
    from erks.models import Project
    from erks.erks_bps.schema.forms import SchemaCollector
    from erks.erks_bps.schema.schema_collectors import DbmsSchemaCollector
    project = Project.objects.get_or_404(id=project_id)
    schema_collector = SchemaCollector.objects.get_or_404(id=schema_collector_id)

    dbms_schema_collector = DbmsSchemaCollector(project=project, schema_collector=schema_collector)
    dbms_schema_collector.collect_schema()
