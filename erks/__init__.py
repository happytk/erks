# -*-encoding:utf-8-*-

"""
====================================
 :erks:`erks` main module
====================================
.. moduleauthor:: chazzy1@sk.com, einslib@sk.com, wecanfly@sk.com
.. note:: nothing special

설명
=====

erks의 main module입니다. wsgi 호환되는 app을 생성할 수 있습니다.

참고
====

참고:
 * http://nexcore-erc.com
 * http://erc.skcc.com

관련 작업자
===========

본 모듈은 다음과 같은 사람들이 관여했습니다:
 * skcc chazzy1@sk.com
 * skcc einslib@sk.com
 * skcc wecanfly@sk.com

작업일지
--------

다음과 같은 작업 사항이 있었습니다:
 * [2017/07/10] - skb 메타구축프로젝트 대응 개선
"""

# import inspect
import logging
import logging.handlers
import os
import random
import sys
import jinja2
import time
from uuid import uuid4

from decorator import decorate  # , decorator

from flask import (
    Flask,
    abort,
    # g,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
    jsonify,
)
# from flask_login import current_user, login_required
# from flask_babel import lazy_gettext
from werkzeug.routing import BaseConverter

# extensions
from erks.extensions import (
    # api,
    # cache,
    # debugtoolbar,
    # docs,
    # edits,
    # flask_log,
    # migrate,
    # plugin_manager,
    # redis_store,
    # scheduler,
    # themes,
    babel,
    breadcrumbs,
    celeryext,
    CORS,
    csrf,
    db,
    jsglue,
    login_manager,
    mail,
    sentry,
    sess,
    swagger,
)
from erks.permissions import (
    VIEWS_FOR_BILLING,
    _build_context,
    _check_permission_project_group,
    _check_permission_project,
    _check_permission_login,
    _check_permission_demo,
    CheckPermissionError,
    SkipCheckPermissionError,
)
from erks.utils import (
    random_hello,
    humanize_datetime,
    humanize_binsize,
    humanize_currency,
    nl2br,
    localized_img_path,
    # flash_error,
)
from erks.models import (
    # Product,
    ProjectGroup,
    Project,
    User,
    # Coupon,
    # Glossary,
    # Term,
    # Post,
    # InfoType,
    # InfoTypeMaster,
    # TermMasterRequest,
    # CodeTermMaster,
    # SiteConfiguration,
)


def _create_app(config=None):
    """create the app(only flask-pure-app)"""

    def select_jinja_autoescape(self, filename):
        """Returns ``True`` if autoescaping should be active for the given
        template name. If no template name is given, returns `True`.

        .. versionadded:: 0.5
        """
        if filename is None:
            return True
        return filename.endswith((
            '.html', '.htm', '.xml', '.xhtml', 'j2'))

    Flask.select_jinja_autoescape = select_jinja_autoescape
    # tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')

    # Initialize the app
    app = Flask(
        __name__,
        static_folder='static',
        # static_url_path='/static',
        # template_folder=tmpl_dir
    )

    # Use the default config and override it afterwards
    # app.config.from_object('flaskbb.configs.default.DefaultConfig')
    app.config.from_object('erks.config')

    # Update the config
    app.config.from_object(config)

    # try to update the config via the environment variable
    app.config.from_envvar("ERKS_SETTINGS", silent=True)
    # app.config.from_object(os.environ.get("ERCC_SETTINGS"))

    return app


def create_app(config=None):
    """Creates the app."""

    app = _create_app(config)

    configure_debug(app)

    # logger는 delayed-creation이므로 이후 사용을 위해 최대한 빨리 설정
    configure_logging(app)
    configure_extensions(app)
    configure_urlmap(app)
    configure_blueprints(app)

    # db_init은 먼저해야 blueprints등록을 할 수 있고,
    # blueprints등록이 끝나야 jsglue를 하면 모든 view를 포함시킬 수 있다.
    jsglue.init_app(app)

    configure_default_data(app)
    configure_template_filters(app)
    configure_context_processors(app)
    # configure_reloaders(app)

    configure_before_handlers(app)
    configure_errorhandlers(app)
    configure_appdir(app)
    configure_meta(app)

    babel.init_app(app)

    # if register_blueprints:
    #     # configure_extensions(app)
    #     configure_default_data(app)

    # @app.route('/post', methods=['POST'])
    # def ajax_post_tst():
    #     from pprint import pprint
    #     from flask import jsonify, request
    #     pprint(request.form.items())
    #     return jsonify(ret='ok')
    # app.logger.debug('helloworld-erc')

    logo = r'''
d sss   d ss.  d     S   sss.
S       S    b S    P  d
S       S    P Ssss'   Y
S sSSs  S sS'  S   s     ss.
S       S   S  S    b       b
S       S    S S     b      P
P sSSss P    P P     P ` ss'
'''  # noqa

    logo_production = r'''
d ss.  d ss.    sSSSs   d ss    d       b   sSSs. sss sssss d   sSSSs   d s  b
S    b S    b  S     S  S   ~o  S       S  S          S     S  S     S  S  S S
S    P S    P S       S S     b S       S S           S     S S       S S   SS
S sS'  S sS'  S       S S     S S       S S           S     S S       S S    S
S      S   S  S       S S     P S       S S           S     S S       S S    S
S      S    S  S     S  S    S   S     S   S          S     S  S     S  S    S
P      P    P   "sss"   P ss"     "sss"     "sss'     P     P   "sss"   P    P
'''  # noqa

    logo_debug = r''''''
    logo_copyright = '\n\n'
    # app.logger.info(logo)
    if app.config['TESTING']:
        pass
    elif app.debug:
        logging.info(logo + logo_debug + logo_copyright)
    else:
        logging.info(logo + logo_production + logo_copyright)

    logging.info('database: %s', app.config['MONGODB_SETTINGS']['DB'])
    # logging.info('billing: %s', app.config['BILLING'])
    logging.info('email-verification: %s',
                 app.config['EMAIL_USER_VERIFICATION'])

    return app


def configure_default_data(app):

    # def _create_product_if_not_exist(product_code, d):
    #     if Product.objects(product_code=product_code).first():
    #         pass
    #     else:
    #         # create!
    #         Product(**d).save()
    #         app.logger.info('product({}) is created'.format(product_code))

    # _create_product_if_not_exist(
    #     'project_unlimited',
    #     dict(
    #         product_code='project_unlimited',
    #         product_name=u'ER-C무제한프로젝트',
    #         description='default_unlimited_project',
    #         support_private=True,
    #         member_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'project_default',
    #     dict(
    #         product_code='project_default',
    #         product_name=u'ER-C무료프로젝트',
    #         description='default free project',
    #         support_private=False,
    #         member_cnt_limit=10
    #     ))
    # _create_product_if_not_exist(
    #     'project_10',
    #     dict(
    #         product_code='project_10',
    #         product_name=u'ER-C유료프로젝트-10',
    #         description='personal-billed-project',
    #         price=20000,
    #         support_private=True,
    #         member_cnt_limit=10,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_default',
    #     dict(
    #         product_code='group_default',
    #         product_name=u'group_default',
    #         description='erc_portal_default_group',
    #         price=0,
    #         support_private=False,
    #         member_cnt_limit=0,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_50',
    #     dict(
    #         product_code='group_50',
    #         product_name=u'ER-C프로젝트그룹-50',
    #         description='',
    #         price=230000,
    #         support_private=False,
    #         member_cnt_limit=50,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_100',
    #     dict(
    #         product_code='group_100',
    #         product_name=u'ER-C프로젝트그룹-100',
    #         description='',
    #         price=420000,
    #         support_private=False,
    #         member_cnt_limit=100,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_200',
    #     dict(
    #         product_code='group_200',
    #         product_name=u'ER-C프로젝트그룹-200',
    #         description='',
    #         price=800000,
    #         support_private=False,
    #         member_cnt_limit=200,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_300',
    #     dict(
    #         product_code='group_300',
    #         product_name=u'ER-C프로젝트그룹-300',
    #         description='',
    #         price=1100000,
    #         support_private=False,
    #         member_cnt_limit=300,
    #         project_cnt_limit=0
    #     ))
    # _create_product_if_not_exist(
    #     'group_unlimited',
    #     dict(
    #         product_code='group_unlimited',
    #         product_name=u'ER-C프로젝트그룹-unlimited',
    #         description='',
    #         price=1500000,
    #         support_private=False,
    #         member_cnt_limit=0,
    #         project_cnt_limit=0
    #     ))

    # from erks.erks_bps.project.models import ProjectGroup
    default_project_group = ProjectGroup.objects(
        slug=app.config['DEFAULT_PROJECT_GROUP_SLUG']).first()
    if default_project_group is None:
        default_project_group = ProjectGroup(
            slug=app.config['DEFAULT_PROJECT_GROUP_SLUG'],
            title=u'ER-C공개포털',
            description='er-c기본그룹',
            join_domain_rules=[],
            join_re_rules=[]
        ).save()

    # from erks.erks_bps.admin.models import SiteConfiguration
    # if SiteConfiguration.objects.count() < 1:
    #     SiteConfiguration().save()

    # from erks.erks_bps.codeset.scripts import make_default_codeset
    # make_default_codeset()

    # migration
    # from erks.erks_bps.project.models import Project, ProjectGroup
    # for project in Project.objects(project_group=None).all():
    #     project.project_group = ProjectGroup.default()
    #     project.save()


def configure_debug(app):
    app.debug = app.config['DEBUG']
    if app.debug:
        # http://stackoverflow.com/questions/41144565/flask-does-not-see-change-in-js-file
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

        # http://stackoverflow.com/questions/13768007/browser-caching-issues-in-flask
        @app.after_request
        def add_header(response):
            """
            Add headers to both force latest IE rendering engine or Chrome Frame,
            and also to cache the rendered page for 10 minutes.
            """
            response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
            response.headers['Cache-Control'] = 'public, max-age=0'

            # logging.critical('cache-contorl set max-age=0')
            return response


def configure_urlmap(app):
    class RegexConverter(BaseConverter):

        def __init__(self, url_map, *items):
            super(RegexConverter, self).__init__(url_map)
            self.regex = items[0]

    class MongoObjRegexConverter(BaseConverter):

        def __init__(self, url_map):
            super(MongoObjRegexConverter, self).__init__(url_map)
            self.regex = "[a-z0-9]{24}"

    # Use the RegexConverter function as a converter
    # method for mapped urls
    app.url_map.converters['regex'] = RegexConverter
    app.url_map.converters['mbj'] = MongoObjRegexConverter


def configure_appdir(app):

    # app-directory check 없으면 생성
    for path in (app.config['ERD_UPLOAD_DIR'],
                 app.config['EXCEL_UPLOAD_DIR'],
                 app.config['LOG_DIR'],
                 ):
        if not os.path.isdir(path):
            os.makedirs(path)


def configure_extensions(app):

    db.init_app(app)
    # edits.init_app(app)
    # flask_log.init_app(app)
    # scheduler.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    breadcrumbs.init_app(app)
    mail.init_app(app)

    # session init전에 mongoclient생성
    app.config['SESSION_MONGODB'] = db.connect()
    sess.init_app(app)

    # swagger.init_app(app)
    # api.init_app(app)
    # cache.init_app(app)
    CORS(app, resources={r"/api_*": {"origins": "*"}})

    # celery.conf.update(app.config)
    celeryext.init_app(app)

    if app.config['SENTRY_USE'] and sentry:
        app.logger.info('SENTRY IS UP')
        sentry.init_app(app, dsn=app.config['SENTRY_DSN'],
                        logging=True, level=logging.ERROR)

    @login_manager.user_loader
    def load_user(userid):
        # from erks.erks_bps.login.models import User
        try:
            return User.objects.get(email=userid)
        except User.DoesNotExist:
            return None
    login_manager.session_protection = "strong"


def configure_template_filters(app):

    # app.jinja_env.autoescape = False
    app.jinja_env.filters['naturalday'] = humanize_datetime
    app.jinja_env.filters['currency'] = humanize_currency
    app.jinja_env.filters['nl2br'] = nl2br
    app.jinja_env.filters['random_hello'] = random_hello
    app.jinja_env.filters['naturalbsize'] = humanize_binsize
    app.jinja_env.filters['localized_img_path'] = localized_img_path
    app.jinja_env.filters['strd_dt_fmt'] = \
        lambda o: o.strftime('%Y-%m-%d %H:%M')
    app.jinja_env.filters['done_icon'] = lambda b: jinja2.Markup(
        '<i class="fa fa-check"></i>' if b else '')

    # def sanitize_html(text):
    #     # return jinja2.Markup(scrubber.Scrubber().scrub(text))
    #     return jinja2.Markup(bleach.clean(text))
    # app.jinja_env.filters['sanitize_html'] = sanitize_html

    def filter_shuffle(seq):
        try:
            result = list(seq)
            random.shuffle(result)
            return result
        except:  # noqa
            return seq
    app.jinja_env.filters['shuffle'] = filter_shuffle

    # @app.template_filter('project_name')
    # def _jinja2_filter_project_name(o):
    #     try:
    #         return project.models.Project.objects.get(id=o).title or u''
    #     except project.models.Project.DoesNotExist:
    #         return u''

    # https://ana-balica.github.io/2014/02/01/autoversioning-static-assets-in-flask/

    # if app.debug:
    #     gen_timestamp = time.time()
    # else:
    #     gen_timestamp = __version__
    gen_timestamp = time.time()

    @app.template_filter('autoversion')
    def autoversion_filter(filename):
        # determining fullpath might be project specific
        # fullpath = os.path.join('some_app/', filename[1:])
        # try:
        #     timestamp = str(os.path.getmtime(fullpath))
        # except OSError:
        #     return filename
        newfilename = "{0}?v={1}".format(filename, gen_timestamp)
        return newfilename


def configure_context_processors(app):
    """
    JINJA내에서 사용할 수 있는 변수 혹은 함수
    """
    @app.context_processor
    def utility_processor():
        def format_3s(number):
            return format(number, ',')
        return dict(format_3s=format_3s, debug=app.debug)

    @app.context_processor
    def project_permission_processor():

        from erks.permissions import (
            is_pg_owner,
            is_pg_moderator,
            is_pg_termer,
            is_p_owner,
            is_p_member,
            is_p_modeler,
            is_p_termer,
            can_be_p_termer,
            can_be_p_modeler,
            can_be_pg_moderator,
            can_be_pg_termer,
        )
        from erks.portlets import erks_portlets
        from erks.utils.portlet import Portlet
        # from erks.erks_bps.project.models import Project, ProjectGroup
        return dict(
            is_pg_owner=is_pg_owner,
            is_pg_moderator=is_pg_moderator,
            is_pg_termer=is_pg_termer,
            is_p_owner=is_p_owner,
            is_p_member=is_p_member,
            is_p_modeler=is_p_modeler,
            is_p_termer=is_p_termer,
            can_be_p_termer=can_be_p_termer,
            can_be_p_modeler=can_be_p_modeler,
            can_be_pg_moderator=can_be_pg_moderator,
            can_be_pg_termer=can_be_pg_termer,
            Project=Project,
            ProjectGroup=ProjectGroup,
            # Coupon=Coupon,
            erks_portlets=erks_portlets,
            Portlet=Portlet,
            uuid=lambda: str(uuid4()).replace('-', ''),
            # site_configuration=SiteConfiguration.objects.first(),
        )

    @app.context_processor
    def project_groups():

        # from erks.erks_bps.project.models import ProjectGroup
        return dict(default_project_group=ProjectGroup.default())


def configure_logging(app):

    if not os.path.isdir(app.config['LOG_DIR']):
        os.makedirs(app.config['LOG_DIR'])

    if not os.path.isdir(app.config['TRANSACTION_LOG_DIR']):
        os.makedirs(app.config['TRANSACTION_LOG_DIR'])

    # https://github.com/pallets/flask/issues/641
    # http://stackoverflow.com/questions/27775026/provide-extra-information-to-flasks-app-logger
    # app.debug_log_format = "(levelname)s in %(module)s [%(pathname)s:%(lineno)d]: %(message)s"
    app.LOGGER_HANDLER_POLICY = 'never'
    # app.logger_name = 'nowhere'
    # app.logger

    log_level = getattr(logging, app.config['LOG_LEVEL'])

    # app.logger.warning('A warning message is sent.')
    # app.logger.error('An error message is sent.')
    # app.logger.info('Information: 3 + 2 = %d', 5)

    log_formatter = logging.Formatter(
        '[%(levelname)8s]'
        # '[%(asctime)s]'
        # '[%(name)s]'
        ' %(message)s'
    )
    log_handlers = []
    if not app.debug:
        log_path = os.path.join(app.config['LOG_DIR'], 'erks.log')
        _unified_hanlder = logging.handlers.TimedRotatingFileHandler(
            log_path,
            when='D',
            interval=1,
            backupCount=90)
        _unified_hanlder.setLevel(log_level)
        _unified_hanlder.setFormatter(log_formatter)
        log_handlers.append(_unified_hanlder)

        # _stream_handler = logging.StreamHandler()
        # _stream_handler.setLevel(log_level)
        # _stream_handler.setFormatter(log_formatter)
        # log_handlers.append(_stream_handler)

    # loggers = []
    # loggers = [app.logger, ]
    loggers = [logging.getLogger(), ]
    # loggers = [logging.getLogger(), app.logger, ]

    for logger in loggers:
        logger.setLevel(log_level)
        for handler in logger.handlers:
            handler.setFormatter(log_formatter)
        for handler in log_handlers:
            logger.addHandler(handler)


def configure_errorhandlers(app):
    @app.errorhandler(404)
    def page_not_found(e):
        """Return a custom 404 error."""
        # return 'Sorry, Nothing at this URL.', 404
        return render_template('error404.html'), 404

    @app.errorhandler(500)
    def application_error500(e):
        """Return a custom 500 error. (internal server error)"""
        return render_template('error500.html'), 500

    @app.errorhandler(503)
    def application_error503(e):
        """Return a custom 503 error. (service unavailable)"""
        return render_template('error503.html'), 503

    @app.errorhandler(401)
    def application_error401(e):
        """Return a custom 401 error. (unautorized)"""
        return render_template('error503.html'), 401

    @app.errorhandler(403)
    def application_error403(e):
        """Return a custom 403 error. (forbidden)"""
        # return 'Sorry, unexpected error: {}'.format(e), 403
        return render_template('error403.html'), 403


def configure_before_handlers(app):
    """Configures the before request handlers."""

    @app.before_request
    def _check_permission():
        if request.endpoint is None or request.endpoint.endswith('.static'):
            return

        '''xhr이 아닌데 _endpoint로 request가 발생할 경우,
        endpoint로 redirect해준다.'''
        if not request.is_xhr and not app.config['TESTING']:
            try:
                bp, endpoint = request.endpoint.split('.')
                if endpoint.startswith('_'):
                    new_endpoint = f'{bp}.{endpoint[1:]}'
                    if new_endpoint in (r.endpoint for r in app.url_map.iter_rules()):
                        return redirect(url_for(new_endpoint, **request.view_args))
            except ValueError:
                pass

        # if request.endpoint.endswith('glossary_master_infotypes'):
        #     import pdb; pdb.set_trace()
        # app.logger.critical(f'{request.endpoint}, {request}')
        try:
            _build_context()
            _check_permission_demo()
            _check_permission_login()
            _check_permission_project_group()
            _check_permission_project()
        except CheckPermissionError as e:
            app.logger.critical(f'{request.endpoint} : request is rejected to check permission')
            # app.logger.critical(f'{request.endpoint}, {request}')
            return e.response
        except SkipCheckPermissionError:
            pass

    @app.before_first_request
    def build_code_context():
        # from erks.permissions import VIEWS_PERMISSION

        def make_abort_404(func):
            def _(f, *args, **kwargs):
                abort(404)
            return decorate(func, _)

        # flask-app에 등록된 모든 view-functions 을 검사한다.
        for url, f in app.view_functions.items():

            if not app.config['BILLING'] and url in VIEWS_FOR_BILLING:
                f = make_abort_404(f)

                # Replace as the wrapped function(f)
                app.view_functions[url] = f
            # elif VIEWS_PERMISSION.get(url, None):
            #     app.view_functions[url] = login_required(f)

    @app.after_request
    def _set_endpoint(resp):
        resp.headers['X-Test-Endpoint'] = request.endpoint
        return resp


def configure_blueprints(app):

    # blueprints setup
    from erks.erks_bps import (
        # erc_legacy,
        login,
        # codeset,
        board,
        project_group,
        project,
        projectuser,
        # erc,
        # report,
        # term,
        # glossary,
        # glossarymaster,
        # infotype,
        # admin,
        portal,
        # model_mgmt,
        # schema,
        # integrity,
        exporter,
        documents,
        typesystem,
        annotation,
    )

    app.register_blueprint(portal.bpapp)
    app.register_blueprint(login.bpapp, url_prefix='/account')
    # app.register_blueprint(codeset.bpapp)
    app.register_blueprint(board.bpapp)
    app.register_blueprint(project.bpapp)
    app.register_blueprint(projectuser.bpapp)
    # app.register_blueprint(model_mgmt.bpapp)
    # app.register_blueprint(term.bpapp)
    # app.register_blueprint(infotype.bpapp)
    # app.register_blueprint(glossary.bpapp)
    # app.register_blueprint(glossarymaster.bpapp)
    # app.register_blueprint(erc.bpapp, url_prefix='/erc')
    app.register_blueprint(project_group.bpapp)
    app.register_blueprint(documents.bpapp)
    app.register_blueprint(typesystem.bpapp)
    app.register_blueprint(annotation.bpapp)
    # app.register_blueprint(report.bpapp)
    # app.register_blueprint(schema.bpapp)
    # app.register_blueprint(integrity.bpapp)
    # app.register_blueprint(exporter.bpapp)

    # api
    # from erks.erks_bps.api import v0 as pump  # legacy
    # from erks.erks_bps.api.v1.btstptbl import configure_api_btstptbl
    # from erks.erks_bps.api.v1.select2 import configure_api_select2
    # from erks.erks_bps.api.v1.skb import configure_api_skb
    # from erks.erks_bps.api_v1 import configure_api_v1
    # from erks.erks_bps.api_v2 import configure_api_v2
    # app.register_blueprint(pump.bpapp)
    # configure_api_btstptbl(app)
    # configure_api_select2(app)
    # configure_api_skb(app)

    # _ = project.models.ProjectGroup.objects(slug='default').first()
    # if _:
    #     project.models.ProjectGroup(slug='default', title=u'기본', description='default').save()
    # app.register_blueprint(erc_legacy.bpapp, url_prefix='/demo')
    # app.register_blueprint(user.bpapp, url_prefix='/user')
    # app.register_blueprint(admin, url_prefix='/erks_adm')

    # finding the erks_components
    # if app.config['TESTING']:
    #     pass
    # else:
    #     try:
    #         from erks_components import bpapp as components_app
    #     except ImportError:
    #         _basedir = os.path.abspath(
    #             os.path.join(
    #                 os.path.dirname(__file__),
    #                 os.path.pardir,
    #                 os.path.pardir
    #             )
    #         )
    #         _ = os.path.join(_basedir, 'erks_components')
    #         if os.path.isdir(_):
    #             sys.path.insert(0, _basedir)
    #             from erks_components import bpapp as components_app
    #         else:
    #             raise Exception("cannot find the 'erks_components' from %s" % _)
    #         del _
    #     # components
    #     app.register_blueprint(components_app, url_prefix='/comp')

    # admin.configure_admin(app)


def configure_meta(app):
    @app.route('/robots.txt')
    def static_from_root():
        return send_from_directory(app.static_folder, request.path[1:])

    @app.route("/api_spec_skb")
    def spec():
        swag = swagger(app)
        swag['info']['version'] = "1.0"
        swag['info']['title'] = "nexcore-erc api(skb)"
        return jsonify(swag)

# def configure_reloaders(app):
#     # from erks.erks_bps.term.models import Term
#     # from erks.erks_bps.login.models import User

#     @app.before_request
#     def register_loaders():
#         register_loader('domain_term', QueryAjaxModelLoader('domain_term', Term, fields=['term_name'], label_attr='term_name'))
#         register_loader('project_group_manager_email', QueryAjaxModelLoader('project_group_manager_email', User, fields=['email'], label_attr='email'))


from ._version import get_versions  # noqa
__version__ = get_versions()['version']
del get_versions
