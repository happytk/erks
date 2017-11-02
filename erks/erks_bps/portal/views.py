# -*- encoding:utf8 -*-
"""
er-c portal views
"""

# import json
import os

from flask_login import current_user
from flask_breadcrumbs import register_breadcrumb
from flask import (
    render_template,
    current_app,
    send_file,
    redirect,
    url_for,
    abort,
    request,
    # jsonify,
    # g,
    # Response,
    session,
)
# from erks.erks_bps.billing.models import Product
from erks.erks_bps.project_group.models import ProjectGroup
from erks.erks_bps.project.models import (
    Project,
)
from erks.erks_bps.login.forms import LoginForm
from . import bpapp


@bpapp.route('/__raise')
def raise_exception_test():
    raise Exception('raise_exception_test')


@bpapp.route('/__503')
def raise_503():
    abort(503)


@bpapp.route('/download/xls/<file_id>', methods=['POST', 'GET'])
def download_file(file_id):
    # filepath = current_app.config[key + '_FILE_PATH']
    # filename = current_app.config[key + '_FILE_NAME']
    filename = file_id + '.xlsx'
    filepath = os.path.join(current_app.config['EXCEL_UPLOAD_DIR'], filename)
    if os.path.isfile(filepath):
        return send_file(filepath,
                         attachment_filename=filename,
                         as_attachment=True)
    else:
        abort(404)


@bpapp.route('/')
def index():
    """index는 현재 사용자의 project_group설정에 따라 이동."""
    # if current_user.is_active and current_user.default_project_group:
    #     return redirect(current_user.default_project_group.url)
    # return redirect(url_for('.default_project_group_index'))
    if current_user.is_active:
        return render_template('portal/myprojects.htm.j2')
    else:
        return render_template('portal/index.htm.j2')


@bpapp.route('/locale/<new_lang_code>')
def new_locale(new_lang_code):
    session['lang_code'] = new_lang_code
    if current_user.is_authenticated:
        current_user.locale = new_lang_code
        current_user.save()
    return redirect(request.referrer)


@bpapp.route('/locale')
def locale():
    return session.get('lang_code', 'ko')

# @bpapp.route('/messages/po/<lang_code>.po')
# def messages_po(lang_code):
#     filepath = os.path.join('erks/translations_js',
#                             lang_code, 'LC_MESSAGES/messages.po')

#     with open(filepath, 'r') as f:
#         read_data = f.read()
#     return read_data


@bpapp.route('/default')
@register_breadcrumb(bpapp, '.', 'Main')
def default_project_group_index():
    # import pdb; pdb.set_trace()
    """login여부에 따라 적절한 index로 이동."""
    slug = current_app.config['DEFAULT_PROJECT_GROUP_SLUG']
    if current_user.is_authenticated:
        return redirect(url_for('project_group.list_projects', slug=slug))
    else:
        projects = Project.random(limit=8)
        project_group = ProjectGroup.default()
        if project_group and project_group.has_theme():
            form = LoginForm(request.form)
            theme_key = project_group.theme_key
            return render_template(
                f'theme/{theme_key}/login/login_{theme_key}.html',
                form=form)
        else:
            return render_template('index.html', projects=projects)


@bpapp.route('/manual')
@bpapp.route('/pg/<slug>/manual')
@bpapp.route('/pg/<slug>/manual/<page>')
def manual(slug=None, page=1):
    """ER-C 소개 페이지."""
    slug = current_app.config['DEFAULT_PROJECT_GROUP_SLUG'] if slug is None else slug
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group and project_group.has_theme():
        theme_key = project_group.theme_key
        return render_template(
            f'theme/{theme_key}/manual/manual_base_{theme_key}.html', project_group=project_group, page=int(page))
    else:
        # nexcore-erc.com 매뉴얼 추가 예정
        return ''


@bpapp.route('/about')
@bpapp.route('/pg/<slug>/about')
def about(slug=None):
    """ER-C 소개 페이지."""
    slug = current_app.config['DEFAULT_PROJECT_GROUP_SLUG'] if slug is None else slug
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template('portal/about.htm.j2', project_group=project_group)


@bpapp.route('/services')
@bpapp.route('/pg/<slug>/services')
def services(slug='default'):
    """상품 소개 페이지. 생성 페이지까지 연결."""
    #     args = {}
    #     args['project_group'] = ProjectGroup.objects.get_or_404(slug=slug)

    #     products = Product.objects.all()
    #     for product in products:
    #         args[product.product_code] = product
    #     return render_template('services.html', **args)
    return render_template('services.html')


@bpapp.route('/search', methods=['GET', 'POST'])
@bpapp.route('/search/<search_string>', methods=['GET', 'POST'])
@bpapp.route('/search/<search_string>/<int:skip>', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/search', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/search/<search_string>', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/search/<search_string>/<int:skip>', methods=['GET', 'POST'])
def search(slug='default', search_string='', skip=0):
    if search_string:
        project_group = ProjectGroup.objects.get_or_404(slug=slug)
        projects = Project.visible_objects(project_group=project_group,
                                           title__icontains=search_string)
        projects = projects.skip(skip).limit(8)

        if project_group.has_theme():
            return render_template('theme/{theme_key}/_project_more_{theme_key}.html'.format(theme_key=project_group.theme_key), projects=projects)
        else:
            return render_template('_project_more.html', projects=projects)
    else:
        return ''


# @bpapp.route('/projects')
# def projects():
#     d = {}
#     d['notices'] = Notice.get_valid_notices()
#     d['project_group'] = ProjectGroup.default()
#     # return render_template('projects.html', **d)
#     return render_template('project_group/list_projects.html', **d)


@bpapp.route('/projects_more/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/projects_more/<search_string>', methods=['GET', 'POST', ])
@bpapp.route('/projects_more/<search_string>/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/projects_more/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/projects_more/<search_string>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/projects_more/<search_string>/<int:skip>', methods=['GET', 'POST', ])
def projects_more(slug='default', search_string='', skip=0):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.visible_objects(project_group=project_group)
    if search_string:
        projects = projects.filter(title__icontains=search_string)
    projects = projects.skip(skip).limit(8)
    return render_template('_project_more.html', projects=projects)


@bpapp.route('/_projects_recommend')
@bpapp.route('/pg/<slug>/_projects_recommend')
def _projects_recommend(slug='default'):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.random(limit=8, project_group=project_group)
    return render_template('_project_more.html',
                           projects=projects)


@bpapp.route('/_projects_picked', methods=['GET', 'POST', ])
@bpapp.route('/_projects_picked/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_picked', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_picked/<int:skip>', methods=['GET', 'POST', ])
def _projects_picked(slug='default', skip=0):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.visible_objects(
        picked=True, project_group=project_group).skip(skip).limit(8)
    return render_template('_project_more.html',
                           projects=projects)


@bpapp.route('/_projects_mine', methods=['GET', 'POST', ])
@bpapp.route('/_projects_mine/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_mine', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_mine/<int:skip>', methods=['GET', 'POST', ])
def _projects_mine(slug='default', skip=0):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.my_belonged(
        project_group=project_group).skip(skip).limit(8)
    projects = [p.project for p in projects]

    if project_group.has_theme():
        return render_template('theme/{theme_key}/_project_more_{theme_key}.html'.format(theme_key=project_group.theme_key), projects=projects)
    else:
        return render_template('_project_more.html', projects=projects)


@bpapp.route('/_projects_all', methods=['GET', 'POST', ])
@bpapp.route('/_projects_all/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_all', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_all/<int:skip>', methods=['GET', 'POST', ])
def _projects_all(slug='default', skip=0):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.visible_objects(
        project_group=project_group).skip(skip).limit(8)

    if project_group.has_theme():
        return render_template('theme/{theme_key}/_project_more_{theme_key}.html'.format(theme_key=project_group.theme_key), projects=projects)
    else:
        return render_template('_project_more.html', projects=projects)


@bpapp.route('/_projects_visited', methods=['GET', 'POST', ])
@bpapp.route('/_projects_visited/<int:skip>', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_visited', methods=['GET', 'POST', ])
@bpapp.route('/pg/<slug>/_projects_visited/<int:skip>', methods=['GET', 'POST', ])
def _projects_visited(slug='default', skip=0):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    projects = Project.my_visit_log(8, skip, project_group=project_group)

    if project_group.has_theme():
        return render_template('theme/{theme_key}/_project_more_{theme_key}.html'.format(theme_key=project_group.theme_key), projects=projects)
    else:
        return render_template('_project_more.html', projects=projects)


# @bpapp.route('/_projects_invited')
# @bpapp.route('/pg/<slug>/_projects_invited')
# def _projects_invited(slug='default'):
#     """TODO: 이 페이지는 이제 사용하지 않습니다.
#        초대된 경우 즉시 가입되기 때문에 더 이상 수락의 의미가 없음
#     """
#     project_group = ProjectGroup.objects.get_or_404(slug=slug)
#     projects = current_user.auto_invited_projects(project_group=project_group)
#     return render_template('_project_more.html',
#                            projects=projects)


@bpapp.route('/_ksnet_rcv', methods=['POST'])
def _project_billing_ksnet_rcv():
    """ksnet-popup을 결과수신 및 팝업창을 닫기 위해 내부적으로 거쳐가는 페이지."""
    args = dict()
    args['rcid'] = request.form.get('reCommConId', None)
    args['rctype'] = request.form.get('reCommType', None)
    args['rhash'] = request.form.get('reHash', None)

    return render_template('billing_rcv.html', **args)


# @bpapp.route('/_m_lookup', methods=['GET', 'POST'])
# def ajax_model_lookup():
#     """ajax_field를 위한 lookup view.

#     TODO: 이 view는 권한체크가 어렵다.
#     TODO: project_id가 내부적으로 들어오면 찾아서 검증하는 형식으로 개선 필요.
#     """
#     name = request.args.get('name')
#     query = request.args.get('query')  # search_text
#     offset = request.args.get('offset', type=int)
#     limit = request.args.get('limit', 10, type=int)

#     loader = g.form_ajax_refs.get(name)
#     if not loader:
#         abort(404)

#     try:
#         options = json.loads(request.args.get('querym'))
#         loader.options = options
#     except ValueError:
#         pass

#     data = [loader.format(m) for m in loader.get_list(query, offset, limit)]
#     return Response(json.dumps(data), mimetype='application/json')


@bpapp.route('/_dialog_privacy_policy', methods=['GET', ])
def dialog_privacy_policy():
    return render_template('dialog_privacy_policy.html')


@bpapp.route('/_dialog_toc', methods=['GET', ])
def dialog_toc():
    return render_template('dialog_toc.html')


@bpapp.route('/_dialog_dont_collect_emails', methods=['GET', ])
def dialog_dont_collect_emails():
    return render_template('dialog_dont_collect_emails.html')


@bpapp.route('/_dialog_privacy_policy_agree', methods=['GET', ])
def dialog_privacy_policy_agree():
    return render_template('dialog_privacy_policy_agree.html')
