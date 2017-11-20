"""운영스크립트관리 for erks."""
import os
import random
import sys
import logging

from flask_script import Server, Shell, Manager, prompt_bool  # noqa
from flask_collect import Collect  # noqa
from erks import create_app  # noqa
from erks.extensions import db  # noqa


app = create_app()
manager = Manager(app)
# celery = make_celery(app)




collect = Collect()
collect.init_app(app)
#collect.init_script(manager)


# Turn on debugger by default and reloader
manager.add_command("runserver", Server(
    use_debugger=app.debug,
    use_reloader=app.debug,
    #     processes=4,
    threaded=True,
    port=16060,
    host='0.0.0.0')
)

# from erks.utils.email import sendmail as sendmail_direct

# @celery.task()
# def sendmail(receiver, title, body):
#     with app.app_context():
#             sendmail_direct(receiver, title, body)


def make_shell_context():
    return_dict = {}
    # grab everything we can possibly import from the models module
    # from erks import models
    from erks import models
    from erks.erks_bps import admin as admin_models
    # from erks.erks_bps.user import models as user_models
    # from erks.erks_bps.board import models as board_models

    def _add(models):
        module_importables = dir(models)
        for importable in module_importables:
            try:
                # mongoengine document
                if (issubclass(getattr(models, importable), db.Document) or
                    issubclass(getattr(models, importable), db.DynamicDocument))\
                        and importable not in return_dict:
                    print('imported', importable)
                    return_dict[importable] = getattr(models, importable)
            except TypeError:
                pass
            except AttributeError:
                print(models, importable)

    _add(models)
    _add(admin_models)

    return_dict['app'] = app
    return_dict['db'] = db
    return return_dict


BANNER = \
    """
--
-- Hello NEXCORE ER-C
--
"""

manager.add_command(
    "shell", Shell(make_context=make_shell_context, banner=BANNER))


@manager.command
def babel():
    os.system('pybabel extract -F i18n/babel.cfg -k lazy_gettext -o i18n/messages.pot erks/erks_bps erks/templates/ erks/portlets.py erks/permissions.py erks/utils/')
    # os.system('pybabel init -i i18n/messages.pot -d erks/translations -l en')
    # os.system('pybabel init -i i18n/messages.pot -d erks/translations -l zh')
    os.system('pybabel update -i i18n/messages.pot -d erks/translations')
    # os.system('pybabel extract -F i18n/babel.cfg -k lazy_gettext -o i18n/messages.pot erks/templates')
    # os.system('pybabel update -i i18n/messages.pot -d erks/translations')
    # os.system('pybabel compile -d erks/translations')

    os.system('pybabel extract -F i18n/babel_js.cfg -o i18n/messages_js.pot erks/erks_bps erks/static_new/js')
    os.system('pybabel update -i i18n/messages_js.pot -d erks/static_new/translations_js')
    # os.system('pybabel compile -d erks/translations')


@manager.command
def list_api(host='http://0.0.0.0:5000', sampling='1000', loglevel='CRITICAL'):
    '''listup api endpoint.
    and search additional information.'''
    from erks.erks_bps.api.v1 import skb
    from inspect import signature

    logger = logging.getLogger('list_api')
    logger.setLevel(getattr(logging, loglevel))

    def _get_api_cls(endpoint, attrname):
        _, cls_ = endpoint.split('.')
        return getattr(getattr(skb, cls_), attrname, None)

    def _func_doc(endpoint):
        doc = _get_api_cls(endpoint, '__doc__')
        return doc.replace('\n', ' ') if doc else '-'

    def _func_has_search(endpoint):
        return ' (./) ' if _get_api_cls(endpoint, 'search') else ' '

    def _func_sig(endpoint):
        args = ','.join(str(
            signature(_get_api_cls(endpoint, 'get'))
        )[1:-1].split(',')[1:]) or '-'
        input_cls = _get_api_cls(endpoint, 'input_cls')
        input_cls_name = input_cls.__name__ if input_cls else ''
        return f'{args}: {input_cls_name}'

    def _func_rsc_type(endpoint):
        _, cls_ = endpoint.split('.')
        return f'`{getattr(skb, cls_).__mro__[1].__name__}`'

    def _to_url(rule):
        input_cls = _get_api_cls(rule.endpoint, 'input_cls')
        if input_cls:
            # sample = input_cls.objects.first()
            sample_stat = {}
            for sample in input_cls.objects.limit(int(sampling)):
                if input_cls.__name__ == 'ProjectGroup':
                    rule_replaced = rule.rule.replace(
                        '<id>',
                        str(sample.slug))
                else:
                    rule_replaced = rule.rule.replace(
                        '<mbj:id>',
                        str(sample.id))

                import requests
                req = requests.get(f'{host}{rule_replaced}')
                if not req.ok:
                    logger.error(f'{host}{rule_replaced} is not working')
                    break
                try:
                    json = req.json()
                except:  # noqa
                    continue

                if isinstance(json, dict) and json.get('total', 0) > 100:
                    sample_stat[f'[[{host}{rule_replaced}|{rule.rule}]]'] = json.get('total')
                elif len(str(json)):
                    sample_stat[f'[[{host}{rule_replaced}|{rule.rule}]]'] = len(str(json))
                else:
                    logger.info('trying another sample object...')

            if sample_stat:
                # import pdb; pdb.set_trace()
                return max(sample_stat, key=sample_stat.get)

        return rule.rule

    rules = [r for r in app.url_map.iter_rules()]
    rules = sorted(rules, key=lambda x: x.rule)

    sep = '||'

    output = (
        sep.join([
            '',
            f'{_to_url(r)}',
            f'{_func_has_search(r.endpoint)}',
            f'{_func_rsc_type(r.endpoint)}',
            f'{_func_sig(r.endpoint)}',
            f'{_func_doc(r.endpoint)}',
            ''
        ])
        for r in rules
        if r.endpoint.startswith('api_skb')
    )

    with open('list_api.moin', 'w') as f:
        f.write('\n'.join(output))


@manager.command
def check_route_config():
    from erks.permissions import VIEWS_PERMISSION
    rules = sorted(app.view_functions.keys())
    print('-' * 80)
    for r in rules:
        if r not in VIEWS_PERMISSION and not r.endswith('.static'):
            print(r)
    print('-' * 80)
    for r in VIEWS_PERMISSION.keys():
        if r not in rules:
            print(r)
    print('-' * 80)


@manager.command
def list_routes():
    rules = sorted(app.view_functions.keys())
    for r in rules:
        print(r)


@manager.command
def update_cover(img_path):
    """
    Make random-profile-images for projects, users
    """
    from erks.erks_bps.login.models import User
    from erks.erks_bps.project.models import Project

    imgs = filter(lambda x: x.endswith('.jpg'), os.listdir(img_path))
    for u in User.objects.all():
        u.profile_imgf = open(
            os.path.join(img_path, random.choice(imgs)), 'rb')
        u.save()
    for p in Project.objects.all():
        p.profile_imgf = open(
            os.path.join(img_path, random.choice(imgs)), 'rb')
        p.save()
    print('done.')


@manager.command
def codesetup(clean=False):

    from erks.erks_bps.glossary.scripts import make_default_codeset
    from erks.erks_bps.glossary.models import CodeSet

    """ Create default codeset """
    if clean and prompt_bool('Are you sure you want to lose all your codeset?'):
        CodeSet.drop_collection()

    make_default_codeset()


# @manager.command
# def celery_worker(detach=False):
#     argv = ['worker', ]
#     if app.config['DEBUG']:
#         argv.append('--loglevel=DEBUG')
#     else:
#         argv.append('--loglevel=INFO')
#     if not app.config['DEBUG'] or detach:
#         argv.append(
#             '--logfile=' + os.path.join(app.config['LOG_DIR'], 'worker.log'))
#     if detach:
#         argv.append('--detach')
#     celery.worker_main(argv)


from erks.erks_bps.project_group.manager import manager as project_group_manager  # noqa
from erks.erks_bps.project.manager import manager as project_manager  # noqa
from erks.erks_bps.login.manager import manager as login_manager  # noqa
from migrate import manager as migrate_manager  # noqa

manager.add_command("project", project_manager)
manager.add_command("project_group", project_group_manager)
manager.add_command("user", login_manager)
manager.add_command("migrate", migrate_manager)

# standalone mode
if __name__ == '__main__':
    manager.run()
# wsgi mode
else:
    pass
