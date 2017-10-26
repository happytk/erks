from .. import bpapp
from datetime import datetime
from dateutil.relativedelta import relativedelta
from erks.utils import flash_error, flash_success  # noqa
from erks.erks_bps.login.models import User
from erks.utils.portlet import Portlet
from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser
from erks.erks_bps.project_group.forms import (
    # ProjectGroupMemberPrefForm,
    # ProjectGroupMemberInviteForm,
    # ProjectGroupManagerInviteForm,
    # ProjectGroupManagerRemoveForm,
    # ProjectGroupSecurityPrefForm,
    # ProjectGroupNoticePrefForm,
    # ProjectGroupProjectPrefForm,
    ProjectGroupInviteMemberForm,
    # ProjectGroupSubscriptionForm,
    # ProjectGroupSubscriptionFormWizardStepTwo,
    # ProjectGroupCreateBillingForm,
    # ProjectGroupCreateBillingFormWizardStepTwo,
    ProjectGroupUserRoleForm,
)
from flask import (
    abort,
    current_app,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user
from flask_babel import lazy_gettext, gettext
from wtforms.validators import ValidationError

import mongoengine
import json
import logging as logger


@bpapp.route('/pg/<slug>', methods=['GET'])
def index(slug):
    return redirect(url_for('.list_projects', slug=slug))


@bpapp.route('/pg/<slug>/_invite_review', methods=['POST'])
def _invite_review(slug):

    form = ProjectGroupInviteMemberForm(request.form)

    if request.method == 'POST' and form.validate():
        return jsonify(form.review_invitations())
    else:
        current_app.logger.debug(form.errors)
        abort(400)


@bpapp.route('/pg/<slug>/_invite', methods=['GET', 'POST'])
def _invite(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if request.method == 'POST':
        form = ProjectGroupInviteMemberForm(request.form)
        project_group = g.project_group

        if request.method == 'POST' and form.validate():
            count_emails = form.count_invitations()
            if count_emails > 20:
                return jsonify(
                    ret=False,
                    message=gettext(u'초대는 최대 20명까지 처리가능합니다.')), 500

            receivers = form.review_invitations()

            # 초대시작
            ret_ok_count = 0
            for r in receivers:
                if r['ok']:
                    try:
                        project_group.join(r['user'])
                        ret_ok_count += 1
                    except mongoengine.errors.NotUniqueError:
                        pass

            if ret_ok_count:
                return jsonify(
                    ret=True,
                    message=lazy_gettext(
                        u'감사합니다. '
                        u'%(ret_ok_count)d명의 사용자가 초대되었습니다.',
                        ret_ok_count=ret_ok_count))
            else:
                return jsonify(
                    ret=False,
                    message=gettext(u'사용자 초대가 실패했습니다.')), 500
        else:
            return jsonify(
                ret=False,
                message=lazy_gettext(u'잘못된 폼 요청입니다.')), 400
    return render_template(
        'project_group/_invite.htm.j2', project_group=project_group)


# @bpapp.route('/pg/<slug>/_user_search', methods=['POST'])
# def _user_search(slug):
#     project_group = ProjectGroup.objects.get_or_404(slug=slug)
#     search_text = request.form['search_text']
#     users = User.objects(
#         Q(name__contains=search_text) |
#         Q(user_no__contains=search_text) |
#         Q(email__contains=search_text)).limit(10)

#     #
#     d = {}
#     d['form'] = ProjectGroupMemberInviteForm(request.form)
#     d['project_group'] = project_group
#     return render_template(
#         'project_group/_invite.html',
#         user_search_text=search_text,
#         user_search_result=users, **d)


@bpapp.route('/_change_default_projectg/')
@bpapp.route('/_change_default_projectg/<slug>')
def change_default_projectg(slug=None):

    try:
        if current_user and current_user.is_active:
            user = current_user._get_current_object()
            if slug:
                pg = ProjectGroup.objects.get(slug=slug)
                user.default_project_group_id = pg.id
            else:
                user.default_project_group_id = None
            user.save()

            return jsonify(ret='ok')
        else:
            return jsonify(ret='fail', message='user is not active')
    except Exception as e:
        return jsonify(ret='fail', mesasge=str(e))


@bpapp.route('/pg/validate_pg_slug', methods=['GET'])
def validate_pg_slug():

    pg_slug = request.args.get('slug')
    if pg_slug and len(pg_slug.strip()):
        pg = ProjectGroup.objects(slug=pg_slug).first()
        if pg:
            return str(pg.id)  # just 200 response.

    abort(404)


@bpapp.route('/pg/pg_create/_ksnet', methods=['POST', 'GET'])
def pg_create_ksnet():

    try:
        seq = int(request.args.get('seq', 1))
    except ValueError:
        seq = 1

    product_code = request.args.get('product_code')
    product = Product.objects.get_or_404(product_code=product_code)

    if seq == 1:
        pg_create_form = ProjectGroupCreateBillingForm(
            request.form,
            product_code=product_code)
        pg_create_form.product_obj.data = product
    elif seq == 2 and request.method == 'POST':
        pg_create_form = ProjectGroupCreateBillingFormWizardStepTwo(
            request.form,
            product_code=product_code)

        try:
            months = int(pg_create_form.subscription_months.data)
        except ValueError:
            months = 1
            pg_create_form.subscription_months.data = months

        pg_create_form.sndAmount.data = product.price * months
        pg_create_form.product_obj.data = product

        # calculate "service-period"
        service_period_start = datetime.now()
        service_period_end = service_period_start + relativedelta(months=months)
        pg_create_form.sndServicePeriod.data = "{0}-{1}".format(
            service_period_start.strftime("%Y%m%d"),
            service_period_end.strftime("%Y%m%d"))
    else:
        abort(403)

    return render_template('project_group/pg_create_ksnet.html',
                           seq=seq,
                           pg_create_form=pg_create_form)


@bpapp.route('/pg/pg_create/_ksnet_result', methods=['POST'])
def pg_create_ksnet_result():

    form = ProjectGroupCreateBillingForm(
        request.form, product_code=request.args.get('product_code'))

    if request.method == 'POST':
        try:
            if form.validate():
                project_group = form.save()
                return render_template(
                    'billing_result.html',
                    purchased_project_group=project_group,
                    **json.loads(form.erks_transaction.data.to_json()))
            else:
                logger.debug(form.errors)
                return render_template(
                    'project_group/pg_create_ksnet.html',
                    pg_create_form=form)
        except ValidationError:
            flash_error(lazy_gettext(u'결제에 문제가 발생했습니다.'))
            return redirect(url_for('portal.index'))


# @bpapp.route('/pg/<slug>/_pg_subscription_log')
# def _pg_subscription_log(slug):
#     project_group = g.project_group
#     log = Order.objects(project_group=project_group).order_by('-pay_when')
#     return render_template(
#         'project_group/_preference_billing_log.htm.j2',
#         project_group=project_group,
#         billing_log=log)


# @bpapp.route('/pg/<slug>/pg_subscription', methods=['GET', 'POST'])
# def pg_subscription(slug):
#     try:
#         seq = int(request.args.get('seq', 1))
#     except ValueError:
#         seq = 1

#     if seq == 1:
#         form = ProjectGroupSubscriptionForm(request.form)
#     elif seq == 2 and request.method == 'POST':
#         form = ProjectGroupSubscriptionFormWizardStepTwo(request.form)
#     else:
#         abort(403)

#     products = Product.objects(
#         product_code__contains="group_",
#         price__gt=0).order_by("price")

#     return render_template(
#         'project_group/pg_subscription.html',
#         pg_billing_form=form,
#         products=products,
#         seq=seq,
#         project_group=g.project_group)


# @bpapp.route('/pg/<slug>/_pg_subscription_ksnet_result', methods=['POST'])
# def _pg_subscription_ksnet_result(slug):

#     form = ProjectGroupSubscriptionForm(request.form)

#     if request.method == 'POST':
#         try:
#             if form.validate():
#                 project_group = form.save()
#                 return render_template(
#                     'billing_result.html',
#                     project_group=project_group,
#                     **json.loads(form.erks_transaction.data.to_json()))
#             else:
#                 logger.warning(form.errors)
#                 return render_template(
#                     'project_group/pg_subscription.html',
#                     pg_billing_form=form,
#                     seq=2,
#                     project_group=g.project_group)
#         except ValidationError:
#             flash_error(lazy_gettext(u'결제에 문제가 발생했습니다.'))
#             return redirect(url_for('project_group.index', slug=slug))


# @bpapp.route('/pg/<slug>/pg_cancel_subscription/<mbj:order_id>', methods=['GET', 'POST'])
# def pg_cancel_subscription(slug, order_id):
#     order = Order.objects.get_or_404(
#         id=order_id,
#         project_group=g.project_group)
#     order.cancel()

#     return redirect(url_for('project_group.preference', slug=slug))


@bpapp.route('/pg/<slug>/projects')
def list_projects(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group.has_theme():
        theme_key = project_group.theme_key
        # template = f'theme/{theme_key}/project_group/list_projects_{theme_key}.html'
        return render_template(
            f'theme/{theme_key}/project_group/list_projects_{theme_key}.html',
            project_group=project_group,
            portlet_summary_projectgroup_notice=Portlet('board._summary_projectgroup_notice', slug=slug),
            portlet_summary_projectgroup_qna=Portlet('board._summary_projectgroup_qna', slug=slug),)
    else:
        # template = 'project_group/list_projects.html'
        return render_template('project_group/list_projects.html', project_group=project_group)


# @bpapp.route('/pg/<slug>/members')
# def list_members(slug):

#     def _try_to_number_or_1(x):
#         try:
#             r = int(x)
#         except ValueError:
#             r = 1
#         return r

#     project_group = ProjectGroup.objects.get_or_404(slug=slug)

#     PER_PAGE = 10
#     member_page = _try_to_number_or_1(request.args.get('mp', 1))

#     d = {}
#     d['project_group'] = project_group
#     d['member_pagination'] = project_group.paginate_field(
#         'members', member_page, PER_PAGE)

#     return render_template('project_group/list_members.html', **d)


@bpapp.route('/pg/<slug>/_delete_brand_img')
def delete_brand_img(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group.brand_imgf:
        project_group.brand_imgf.delete()
        project_group.brand_imgf = None
        project_group.save()
    return redirect(url_for('project_group.preference', slug=slug))


@bpapp.route('/pg/<slug>/_delete_banner_img')
def delete_banner_img(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group.banner_imgf:
        project_group.banner_imgf.delete()
        project_group.banner_imgf = None
        project_group.save()
    return redirect(url_for('project_group.preference', slug=slug))


@bpapp.route('/pg/<slug>/banner.img')
def banner_img(slug, thumbnail=False):
    try:
        project_group = ProjectGroup.objects.only('banner_imgf').get(slug=slug)
    except ProjectGroup.DoesNotExist:
        project_group = None

    try:
        if (
            thumbnail and
            project_group.banner_imgf and
            project_group.banner_imgf.thumbnail
        ):
            image_binary = project_group.banner_imgf.thumbnail.read()
        elif project_group.banner_imgf:
            image_binary = project_group.banner_imgf.read()
        else:
            image_binary = None
    except IOError:
        image_binary = None

    if image_binary:
        response = make_response(image_binary)
        response.headers['Content-Type'] = 'image/jpeg'
        content = 'attachment; filename=banner-%s.jpg' % (slug)
        response.headers['Content-Disposition'] = content
        return response
    else:
        if thumbnail:
            filename = 'img/project_card_default_thumbnail.png'
        else:
            filename = 'img/project_card_default.png'
        return redirect(url_for('static', filename=filename))


@bpapp.route('/pg/<slug>/brand.img')
def brand_img(slug, thumbnail=False):
    try:
        project_group = ProjectGroup.objects.only('brand_imgf').get(slug=slug)
    except ProjectGroup.DoesNotExist:
        project_group = None

    try:
        if (
            thumbnail and
            project_group.brand_imgf and
            project_group.brand_imgf.thumbnail
        ):
            image_binary = project_group.brand_imgf.thumbnail.read()
        elif project_group.brand_imgf:
            image_binary = project_group.brand_imgf.read()
        else:
            image_binary = None
    except IOError:
        image_binary = None

    if image_binary:
        response = make_response(image_binary)
        response.headers['Content-Type'] = 'image/jpeg'
        content = 'attachment; filename=brand-%s.jpg' % (slug)
        response.headers['Content-Disposition'] = content
        return response
    else:
        if thumbnail:
            filename = 'img/project_card_default_thumbnail.png'
        else:
            filename = 'img/project_card_default.png'
        return redirect(url_for('static', filename=filename))


@bpapp.route('/pg/<slug>/_info')
def _info(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template(
        'project_group/_info.htm.j2',
        project_group=project_group)


@bpapp.route('/pg/<slug>/_member_role_action', methods=['POST'])
def member_role_action(slug):
    action = request.form['action']
    if action == 'invite_member':  # invite_member
        user_id = request.form['user_id']
        user = User.objects.get_or_404(pk=user_id)
        pgu = ProjectGroupUser(user=user, project_group=g.project_group).save()
        return render_template(
            pgu.render_template_path,
            project_group_user=pgu)
    elif action == 'moderator_p':
        project_group_user_id = request.form['project_group_user_id']
        pgu = ProjectGroupUser.objects.get_or_404(
            id=project_group_user_id,
            project_group=g.project_group)
        pgu.is_moderator = True
        pgu.save()
        return render_template(
            pgu.render_template_path,
            project_group_user=pgu)
    elif action == 'moderator_m':
        project_group_user_id = request.form['project_group_user_id']
        pgu = ProjectGroupUser.objects.get_or_404(
            id=project_group_user_id,
            project_group=g.project_group)
        pgu.is_moderator = False
        pgu.save()
        return render_template(
            pgu.render_template_path,
            project_group_user=pgu)
    elif action == 'ban':
        project_group_user_id = request.form['project_group_user_id']
        pgu = ProjectGroupUser.objects.get_or_404(
            id=project_group_user_id,
            project_group=g.project_group)
        pgu.delete()
        return ('''
            <td>-</td>
            <td colspan="6">
                {0} 사용자가 제외되었습니다.
            </td>'''.format(pgu.user))

    abort(400)


@bpapp.route('/pgu/<mbj:project_group_user_id>/_role_changer',
             methods=['GET', 'POST'])
def _user_role_changer(project_group_user_id):
    pgu = ProjectGroupUser.objects.get_or_404(id=project_group_user_id)
    if request.method == 'POST':
        form = ProjectGroupUserRoleForm(request.form)
        if form.validate():
            flash_success(gettext('정상적으로 처리되었습니다.'))
            form.populate_obj(pgu)
            pgu.save()
    else:
        form = ProjectGroupUserRoleForm(obj=pgu)

    return render_template(
        'project_group/_role_changer.html',
        form=form,
        project_group_user=pgu)


@bpapp.route('/pgu/<mbj:project_group_user_id>/_user_password_reset',
             methods=['GET'])
def _user_password_reset(project_group_user_id):
    pgu = ProjectGroupUser.objects.get_or_404(id=project_group_user_id)
    if pgu.project_group == ProjectGroup.default():
        from uuid import uuid4
        from erks.utils import password_hash

        temporary_passwd = str(uuid4())[:8]
        pgu.user.password = password_hash(temporary_passwd)
        pgu.user.save()
        flash_error(gettext('임시비밀번호가 설정되었습니다. 암호는 %(temporary_passwd)s입니다.', temporary_passwd=temporary_passwd))
        return redirect(url_for(
            'project_group._user_role_changer',
            project_group_user_id=project_group_user_id))
    else:
        abort(404)


# @bpapp.route('/pg/<slug>/_recent_master_term_requests',
#              methods=['GET', 'POST'])
# def _recent_master_term_requests(slug):
#     project_group = ProjectGroup.objects.get_or_404(slug=slug)
#     return render_template(
#         'project_group/_recent_master_term_requests.html',
#         term_requests=project_group.queryset_master_term_request.limit(5))


@bpapp.route('/pgu/<mbj:project_group_user_id>/leave', methods=['GET'])
def user_leave(project_group_user_id):
    pgu = ProjectGroupUser.objects.get_or_404(id=project_group_user_id)
    # 권한체크
    project_group_current_user = pgu.project_group.queryset_project_group_user.get(
        user=current_user._get_current_object())
    if project_group_current_user.is_moderator or project_group_current_user.is_owner:
        pgu.delete()
        flash_success(gettext(u'%(user_email)s 사용자는 더 이상 프로젝트그룹의 구성원이 아닙니다.', user_email=pgu.user_email))
        return redirect(url_for(
            'project_group.preference_members',
            slug=pgu.project_group.slug))
    else:
        abort(403)  # forbidden

@bpapp.route('/pg/<slug>/_layout',
             methods=['POST'])
def project_group_layout(slug):
    pgu = ProjectGroupUser.objects(
        project_group=g.project_group,
        user=current_user._get_current_object()).first()
    pgu.project_layout = request.form.get('what', 'boxed')
    pgu.save()
    return jsonify(ret='ok')
