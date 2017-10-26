# -*-encoding: utf-8 -*-


from flask_mongoengine import MongoEngine
db = MongoEngine()

# from flask_edits import Edits  # noqa: E402
# edits = Edits()


from flask_login import LoginManager  # noqa: E402
login_manager = LoginManager()

from flask_babel import Babel    # noqa: E402
from flask import (
    g,
    request,
    session,
    current_app,
)   # noqa: E402

babel = Babel()


@babel.localeselector
def get_locale():
    if current_app.debug:
        avaliable_langs = ['ko', 'en', 'zh']
        if 'lang_code' not in session.keys() or session.get('lang_code', 'ko') not in avaliable_langs:
            session['lang_code'] = 'ko'
        g.lang_code = session['lang_code']
        return g.get('lang_code', 'ko')
    else:
        session['lang_code'] = 'ko'
        g.lang_code = session['lang_code']
        return 'ko'


from flask_session import Session
sess = Session()

from flask_cors import CORS  # noqa
# from flask_apscheduler import APScheduler
# scheduler = APScheduler()


# from flask.ext.log import Logging
# flask_log = Logging()

from flask_wtf import CSRFProtect  # noqa: E402
csrf = CSRFProtect()


from flask_jsglue import JSGlue  # noqa: E402
jsglue = JSGlue()


from flask_mail import Mail  # noqa: E402
mail = Mail()


import wtforms_json  # noqa: E402
wtforms_json.init()


try:
    from raven.contrib.flask import Sentry
    sentry = Sentry()
except ImportError:
    sentry = None


import flask_menu  # noqa


def register_breadcrumb_view_g_context():
    from flask import g
    '''flask_breadcrumb의 register_breadcrumb이 참조할 수 있는
    g-context의 일부 정보를 생성;
    url을 단축하면서 project_id와 같은 정보가 사라지고 g를 통해서 볼 수 있다.'''
    d = {}
    if hasattr(g, 'project_group') and g.project_group:
        d['slug'] = g.project_group.slug
        # d.append(dict(text=g.project_group.title, url=g.project_group.url))
    if hasattr(g, 'project') and g.project:
        d['project_id'] = g.project.id
        # d.append(dict(text=g.project.title, url=g.project.url))
    if hasattr(g, 'glossary') and g.glossary:
        d['glossary_id'] = g.glossary.id
        # d.append(dict(text=g.glossary.glossary_name, url=g.glossary.url))
    if hasattr(g, 'term') and g.term:
        d['term_id'] = g.term.id
    if hasattr(g, 'post') and g.post:
        d['post_id'] = g.post.id

    d.update(request.view_args)

    from flask import current_app
    current_app.logger.debug(d)
    return d


# def dynamic_list_constructor_for_ercc(*args, **kwargs):
#     from flask import current_app
#     current_app.logger.debug(args)
#     current_app.logger.debug(kwargs)
#     return [{'text': 'textaaaaaaaa', 'url': ''}]


''' monkey-patching for flask_breadcrumb
flask_breadcrumb의 register_breadcrumb을 패치한 함수
dynamic_list_constructor이 비어있으면 g_context보는 함수로 기본 설정'''
_real_register_menu = flask_menu.register_menu


def _patched_register_menu(app,
                           path,
                           text,
                           order=0,
                           endpoint_arguments_constructor=None,
                           dynamic_list_constructor=None,
                           active_when=None,
                           visible_when=None,
                           **kwargs):
    if endpoint_arguments_constructor is None:
        endpoint_arguments_constructor = register_breadcrumb_view_g_context
    # if dynamic_list_constructor is None:
    #     dynamic_list_constructor = dynamic_list_constructor_for_ercc
    return _real_register_menu(app,
                               path,
                               text,
                               order,
                               endpoint_arguments_constructor,
                               dynamic_list_constructor,
                               active_when,
                               visible_when,
                               **kwargs)


flask_menu.register_menu = _patched_register_menu


# flask_breadcrumbs는 내부적으로 flash_menu를 사용하므로
# 선언하기 전에 flash_menu를 미리 patch해두어야 함.
from flask_breadcrumbs import Breadcrumbs  # noqa: E402
breadcrumbs = Breadcrumbs()


from flask_celeryext import FlaskCeleryExt  # noqa
celeryext = FlaskCeleryExt()

# from celery import Celery  # noqa: E402
# import config  # noqa
# celery = Celery(__name__, broker=config.CELERY_BROKER_URL)

# def make_celery(app):
#     celery = Celery(app.import_name, backend=app.config['CELERY_BACKEND'],
#                     broker=app.config['CELERY_BROKER_URL'],
#                     include=['ercc.tasks'])
#     celery.conf.update(app.config)
#     TaskBase = celery.Task  # noqa: N806

#     class ContextTask(TaskBase):
#         abstract = True

#         def __call__(self, *args, **kwargs):
#             with app.app_context():
#                 return TaskBase.__call__(self, *args, **kwargs)
#     celery.Task = ContextTask
#     return celery

from flask_swagger import swagger  # noqa
