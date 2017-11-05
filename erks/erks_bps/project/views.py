# -*-encoding:utf8 -*-
# pylint: disable=maybe-no-member
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
from bson import ObjectId
import json
from collections import Counter
from erks.utils.portlet import Portlet

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    abort,
    g,
    current_app,
    jsonify,
)
from flask_login import current_user
from flask_babel import lazy_gettext, gettext

from erks.utils import (
    flash_error,
    flash_success,
    flash_warning,
    flash_info,
    register_breadcrumb,
    default_breadcrumb_root
)
from erks.erks_bps.login.models import User
# from erks.erks_bps.billing.models import Order, Coupon
# from erks.erks_bps.projectuser.models import (
#     ProjectUserBase,
#     ProjectUser,
# )
from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser
from erks.erks_bps.project.models import (
    Project,
    ProjectSummary,
    # ProjectNotification,
)
from . import bpapp
from .forms import (
    ProjectEditForm,
    ProjectCreateForm,
    ProjectDeleteForm,
    ProjectSubscriptionForm,
    ProjectSubscriptionFormWizardStepTwo,
    ProjectEditForProjectGroupForm,
    ProjectSubscribeForm,
    RequestMemberForm,
    InviteMemberForm,
    SearchMemberForm,
    # ProjectPlusCreateForm,
    # ProjectPlusCreateFormWizardTwoStep,
    # ProjectPlusCouponCreateForm,
    DelegateProjectOwnerForm,
)
from mongoengine import ValidationError


default_breadcrumb_root(bpapp, '.')


@bpapp.route('/p/<mbj:project_id>/glossarymaster')
def glossary_master_view(project_id):
    from erks.models import GlossaryDerived
    gmd = GlossaryDerived.head_objects(project=g.project).first()
    # todo: 삭제해도 됨. on_created_project에 걸어두었음.
    if gmd is None:
        gmd = g.project.create_glossary_derived()

    return redirect(url_for(
        'glossary_master.glossary_derived_view',
        glossary_derived_id=gmd.id))
    # return render_template('project/not_seen.html', project=g.project)


@bpapp.route('/p/<mbj:project_id>/not_seen')
def not_seen(project_id):
    return render_template('project/not_seen.html', project=g.project)


@bpapp.route('/pg/default/create_project', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/create_project', methods=['GET', 'POST'])
def create_project(slug='default'):

    project_create_form = ProjectCreateForm(request.form)

    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    project_create_form.project_group.data = project_group

    d = {}
    d['form'] = project_create_form
    d['project_group'] = project_group
    # if project_group.is_not_default:
    #     grade = project_group.get_grade(current_user._get_current_object())
    #     if not project_group.ban_create_project or grade in ('owner', 'manager'):
    #         pass
    #     else:
    #         flash_warning(gettext(u'신규 프로젝트 생성 제한 설정중입니다. 그룹관리자에게 문의해주세요.'))
    #         return redirect(url_for('project_group.index', slug=slug))

    # if not current_user.can_make_project_for(project_group):
    #     flash_warning(lazy_gettext(u'더 이상 무료 프로젝트를 생성할 수 없습니다.'))
    #     if current_app.config['BILLING']:
    #         return redirect(url_for('portal.services'))
    #     else:
    #         return redirect(url_for('portal.index'))

    if request.method == 'POST':
        if project_create_form.validate():
            # del project_create_form.subscription_months
            # del project_create_form.billed
            flash_success(gettext(u'프로젝트가 생성되었습니다.'))
            prj = project_create_form.save(commit=False)
            prj.visible = True
            prj.save()
            return redirect(url_for('project.index', project_id=prj.id))
        else:
            flash_error(gettext('프로젝트 생성에 실패했습니다.'))
            return redirect(url_for('portal.index'))
    return render_template('portal/project_create.htm.j2', **d)


# @bpapp.route('/p/p_createplus', methods=['GET', 'POST'])
# def create_project_plus():
#     """과금프로젝트 생성에 사용되는 view."""

#     try:
#         seq = int(request.args.get('seq', 1))
#     except ValueError:
#         seq = 1

#     coupon_event_id = request.args.get('coupon_event_id')
#     if coupon_event_id and seq == 1:
#         if Coupon.available_to_get(coupon_event_id, current_user._get_current_object()):
#             coupon = Coupon.objects(
#                 group_id=coupon_event_id, used_by=None).first()
#             if coupon is not None:
#                 project_create_form = ProjectPlusCouponCreateForm(
#                     request.form, coupon=coupon)
#             else:
#                 flash_error(gettext(u'사용가능한 쿠폰이 없습니다.'))
#                 return redirect(url_for('portal.index'))
#         else:
#             flash_error(gettext(u'사용가능한 쿠폰이 없습니다.'))
#             return redirect(url_for('portal.index'))
#     elif seq == 1:
#         project_create_form = ProjectPlusCreateForm(request.form)
#     elif seq == 2 and request.method == 'POST':
#         project_create_form = ProjectPlusCreateFormWizardTwoStep(request.form)
#     else:
#         abort(403)

#     return render_template('project_group/project_create_plus.html',
#                            seq=seq,
#                            coupon_event_id=coupon_event_id,
#                            project_create_form=project_create_form,
#                            project_group=ProjectGroup.default())


# @bpapp.route('/p/p_createplus_coupon', methods=['POST'])
# def create_project_plus_coupon_result():
#     '''과금되는 프로젝트 생성을 쿠폰을 이용하여 처리합니다.'''

#     form = ProjectPlusCouponCreateForm(request.form)
#     if request.method == 'POST':
#         if form.validate():
#             project = form.save()
#             flash_success(lazy_gettext(u'쿠폰결제가 완료되었습니다.'))
#             return redirect(url_for('project.index', project_id=project.id))
#         else:
#             current_app.logger.debug(form.errors)
#             flash_error(lazy_gettext(u'폼정보가 유효하지 않습니다.'))
#             coupon_event_id = form.coupon.data.group_id
#             return render_template('project_group/project_create_plus.html',
#                                    seq=1,
#                                    coupon_event_id=coupon_event_id,
#                                    project_create_form=form,
#                                    project_group=ProjectGroup.default())

#     else:
#         abort(400)


# @bpapp.route('/p/p_createplus_result', methods=['POST'])
# def create_project_plus_result():
#     """과금되는 프로젝트 생성을 처리합니다."""

#     form = ProjectPlusCreateForm(request.form)
#     form.project_group.data = ProjectGroup.default()

#     if request.method == 'POST':
#         try:
#             if form.validate():
#                 project = form.save()
#                 # g.project = project
#                 return render_template(
#                     'billing_result.html',
#                     purchased_project=project,
#                     **json.loads(form.erks_transaction.data.to_json()))
#             else:
#                 current_app.logger.warning(form.errors)
#                 return render_template(
#                     'project_group/project_create_plus.html',
#                     project_create_form=form)
#         except ValidationError:
#             # 이 경우는 TRANSACTION에 문제가 있는 것임.
#             flash_error(gettext(u'결제에 문제가 발생했습니다.'))
#             return redirect(url_for('portal.index'))


# @bpapp.route(gettext(u'/demo'))
# def demo():
#     """Choose one of demo-projects"""

#     demo_project = Project.demo_objects().first()
#     if demo_project:
#         from erks.erks_bps.erc.models import SubjectArea
#         sa = SubjectArea.objects(prjId=str(demo_project.id)).only('id').first()
#         if sa:
#             return redirect(url_for('erc.ercapp', project_id=demo_project.id, subjId=sa.id))
#         else:
#             return redirect(url_for('erc.ercapp', project_id=demo_project.id))
#     else:
#         flash('Sorry! No demo projects.')
#         return redirect(url_for('portal.index'))


def view_project_dlc(*args, **kwargs):
    return [dict(text=g.project.title, url=g.project.url)]


@bpapp.route('/p/<mbj:project_id>')
@register_breadcrumb(bpapp, '.', lazy_gettext(u'내 프로젝트 홈'), dynamic_list_constructor=view_project_dlc)
def index(project_id):

    project = Project.objects.get_or_404(id=project_id)

    # 이 화면은 비로그인 사용자도 프로젝트 설정에 따라 볼 수 있으므로
    # current_user체크를 해주어야 함
    # project.write_visit_log(current_user._get_current_object())
    # project권한체크시에 넣어줄수도 있지만 굳이 성능이슈를 야기할 필요는 없으므로
    # index에서만 방문일을 갱신
    if current_user and current_user.is_active:
        from erks.models import ProjectUser
        puser = ProjectUser.objects(
            project=project,
            user=current_user._get_current_object()).first()
        if puser:
            puser.visit()

    flash_success('helloworld[category-success]')
    flash_error('helloworld[category-error]')
    flash_info('helloworld[category-info]')
    flash_warning('helloworld[category-warning]')

    # if project.project_group.has_theme():
    #     return render_template(
    #         'theme/{theme_key}/project/index_{theme_key}.html'.format(theme_key=project.project_group.theme_key),
    #         project=project,
    #         portlet_summary_model=Portlet('._summary_model', project_id=project_id),
    #         portlet_summary_glossary=Portlet('._summary_glossary', project_id=project_id),
    #         portlet_subjectarea_recently_changed=Portlet('._subjectarea_recently_changed', project_id=project_id),
    #         portlet_summary_board=Portlet('._summary_board', project_id=project_id),
    #     )
    # else:
    return render_template('project/community.htm.j2', project=project)


@bpapp.route('/p/<mbj:project_id>/info', methods=['GET', 'POST'])
def info(project_id):
    project = Project.objects.get_or_404(id=project_id)
    if request.method == 'POST':
        form = ProjectEditForm(request.form)
        if form.validate():
            form.populate_obj(project)
            project.save()
            flash('Saved the project successfully.')
        else:
            flash('Sorry, There are invalid form data.')
    else:
        form = ProjectEditForm(obj=project)
    return render_template('project/info.htm.j2', project=project, form=form)

@bpapp.route('/p/<mbj:project_id>/_summary_model/_json')
def _summary_model_json(project_id):
    return jsonify(ProjectSummary.get_erc_info(g.project))


@bpapp.route('/p/<mbj:project_id>/_summary_model')
def _summary_model(project_id):
    d = {}
    d['project'] = g.project
    d['entities_info'] = ProjectSummary.get_erc_info(g.project)

    if g.project.project_group.has_theme():
        return render_template('theme/{theme_key}/project/_summary_model_{theme_key}.htm.j2'.format(theme_key=g.project.project_group.theme_key), **d)
    else:
        return render_template('project/_summary_model.htm.j2', **d)


@bpapp.route('/p/<mbj:project_id>/_summary_glossary')
def _summary_glossary(project_id):

    d = {}
    d['project'] = g.project
    d['glossaries_info'] = ProjectSummary.get_glossary_info(g.project)

    if g.project.project_group.has_theme():
        return render_template('theme/{theme_key}/project/_summary_glossary_{theme_key}.htm.j2'.format(theme_key=g.project.project_group.theme_key), **d)
    else:
        return render_template('project/_summary_glossary.htm.j2', **d)


@bpapp.route('/p/<mbj:project_id>/_subjectarea_recently_changed')
def _subjectarea_recently_changed(project_id):
    d = {}
    d['project'] = g.project
    d['entities_info'] = ProjectSummary.get_erc_info(g.project)
    return render_template('project/_subjectarea_recently_changed.htm.j2', **d)


@bpapp.route('/p/<mbj:project_id>/_summary_board')
def _summary_board(project_id):
    # discussion recentchanges
    from erks.erks_bps.board.models import ProjectPost
    posts = ProjectPost.objects(project=g.project, use_yn=True).exclude(
        'contents').order_by('-created_at').limit(5)
    post_cnt = ProjectPost.objects(project=g.project, use_yn=True).count()

    d = {}
    d['posts'] = posts
    d['post_cnt'] = post_cnt
    d['project'] = g.project

    if g.project.project_group.has_theme():
        # return render_template(
        #     'report/_model_glossary_report.htm.j2',
        #     project=g.project,
        #     project_model_report=project_model_report)
        # return render_template('theme/{theme_key}/project/summary_board_{theme_key}.html'.format(theme_key=g.project.project_group.theme_key), **d)
        return render_template('project/_summary_board.htm.j2', **d)
    else:
        return render_template('project/_summary_board.htm.j2', **d)


# @bpapp.route('/p/<mbj:project_id>/_summary_notification')
# def _summary_notification(project_id):

#     # project notification
#     notifications = ProjectNotification.objects(
#         project=g.project).order_by('-created_at').limit(30)

#     d = {}
#     d['notifications'] = notifications
#     d['project'] = g.project
#     return render_template('project/summary_notification.html', **d)


@bpapp.route('/p/<mbj:project_id>/members')
@register_breadcrumb(bpapp, '.members', lazy_gettext(u'회원관리'))
def members(project_id):
    return render_template(
        'project/portlets.htm.j2',
        active_page='members',
        portlets=[
            Portlet('project._members', project_id=project_id)
        ],
    )


@bpapp.route('/p/<mbj:project_id>/pref', methods=['GET', ])
@register_breadcrumb(bpapp, '.preference', lazy_gettext(u'프로젝트 설정'))
def preference(project_id):
    portlets = [
        Portlet('project._preference', project_id=project_id),
    ]
    if current_app.config['BILLING'] and g.project.project_group.is_default:
        portlets.append(Portlet('project._subscription_log', project_id=project_id))

    return render_template(
        'project/portlets.htm.j2',
        active_page='setting',
        portlets=portlets,
    )


@bpapp.route('/p/<mbj:project_id>/_pref', methods=['GET', 'POST'])
def _preference(project_id):
    project = Project.objects.get_or_404(id=project_id)
    if request.method == 'POST':
        form = ProjectEditForm(request.form)
        if form.validate():
            form.populate_obj(project)
            project.save()
            flash_success(lazy_gettext(u'프로젝트 설정이 저장되었습니다'))
    else:
        form = ProjectEditForm(obj=project)

    return render_template(
        'project/_preference.htm.j2',
        form=form,
        project_delete_form=ProjectDeleteForm(obj=project),
        project_owner_delegate_form=DelegateProjectOwnerForm(),
        project=project)


@bpapp.route('/p/<mbj:project_id>/_pgadmin', methods=['GET', 'POST'])
@register_breadcrumb(bpapp, '.preference', lazy_gettext(u'프로젝트 설정'))
def _preference_for_projectgroup(project_id):
    project = Project.objects.get_or_404(id=project_id)
    if request.method == 'POST':
        form = ProjectEditForProjectGroupForm(request.form)
        if form.validate():
            form.populate_obj(project)
            project.save()
            flash(gettext(gettext(u'프로젝트 설정이 저장되었습니다')))
        else:
            flash(gettext(gettext(u'폼 정보에 문제가 있습니다.')))
    else:
        form = ProjectEditForProjectGroupForm(obj=project)

    return render_template(
        'project/_preference_for_projectgroup.htm.j2',
        form=form,
        project=project)


@bpapp.route('/p/<mbj:project_id>/_invite_review', methods=['POST', 'GET'])
def _invite_review(project_id):

    form = InviteMemberForm(request.form)

    if request.method == 'GET':
        return redirect(url_for('._invite', project_id=project_id))
    elif request.method == 'POST' and form.validate():
        # return jsonify(form.review_invitations())
        review = form.review_invitations()
        review_ok = any(map(lambda x: x['ok'], review))
        return render_template(
            'project/_invite.htm.j2',
            project=g.project,
            form=form,
            review=review,
            review_ok=review_ok)
    else:
        current_app.logger.debug(form.errors)
        abort(400)


@bpapp.route('/p/<mbj:project_id>/_invite', methods=['GET', 'POST'])
def _invite(project_id):

    if request.method == 'POST':
        form = InviteMemberForm(request.form)
        project = g.project
        project_group = g.project_group

        if form.validate():
            count_emails = form.count_invitations()
            if count_emails > 20:
                return jsonify(
                    ret=False,
                    message=gettext(u'초대는 최대 20명까지 처리가능합니다.')), 500
            elif not project.is_new_member_available(
                    new_member_cnt=count_emails):
                return jsonify(
                    ret=False,
                    message=gettext(u'허용된 회원 수를 초과하여 초대할 수 없습니다.')), 500

            receivers = form.review_invitations()

            # 초대시작
            ret_ok = Counter([
                project.invite(
                    r['user_email'],
                    inviter=current_user._get_current_object()
                ) for r in receivers if r['ok']])
            ret_ok_count = ret_ok.get(True, 0)

            # outbound초대시작
            if project_group.can_invite_oubound_user:
                ret_email = Counter([
                    project.invite(
                        r['user_email'],
                        inviter=current_user._get_current_object()
                    ) for r in receivers if r['user'] is None])
                ret_ok_count += ret_email.get(True, 0)

            if ret_ok_count:
                # return jsonify(
                #     ret=True,
                #     message=lazy_gettext(
                #         u'감사합니다. '
                #         u'%(ret_ok_count)d명의 사용자가 초대되었습니다.',
                #         ret_ok_count=ret_ok_count))
                flash_success(gettext(
                    u'%(ret_ok_count)d명의 사용자가 초대되었습니다.',
                    ret_ok_count=ret_ok_count))
                return redirect(url_for('._invite', project_id=project_id))
            else:
                # return jsonify(
                #     ret=False,
                #     message=gettext(u'사용자 초대가 실패했습니다.')), 500
                flash_error(gettext(u'사용자 초대가 실패했습니다.'))
        else:
            # import pdb; pdb.set_trace()
            # return jsonify(
            #     ret=False,
            #     message=lazy_gettext(u'잘못된 폼 요청입니다.')), 400
            flash_error(gettext(u'잘못된 폼 요청입니다.'))
    else:
        form = InviteMemberForm()

    return render_template('project/_invite.htm.j2', project=g.project, form=form)


@bpapp.route('/p/<mbj:project_id>/_subscribe', methods=['GET', 'POST'])
def _subscribe(project_id):
    from erks.models import ProjectUserReportSubscription

    project = Project.objects.get_or_404(id=project_id)
    pu = ProjectUserReportSubscription.objects(
        project=project,
        user=current_user._get_current_object()).first()
    if pu is None:
        pu = ProjectUserReportSubscription(
            project=project,
            user=current_user._get_current_object())

    if request.method == 'POST':
        form = ProjectSubscribeForm(request.form)
        form.populate_obj(pu)
        if any([
                pu.subscribed_report_model_glossary,
                pu.subscribed_report_model_schema,
                pu.subscribed_report_model_change]):
            pu.save()
        elif pu.id:
            pu.delete()
        flash_success(gettext(u'저장되었습니다.'))
    else:
        form = ProjectSubscribeForm(obj=pu)

    return render_template(
        'project/_subscribe.htm.j2',
        form=form,
        subscription_cnt=ProjectUserReportSubscription.objects(project=project).count(),
        project=project)


@bpapp.route('/p/<mbj:project_id>/_join_request', methods=['POST', ])
def join_request(project_id):
    """사용자의 가입요청"""

    project = Project.objects.get_or_404(id=project_id)
    form = RequestMemberForm(request.form)

    if request.method == 'POST' and form.validate():
        if current_user in project.members:
            flash_warning(lazy_gettext(u'이미 등록된 사용자입니다.'))
        elif current_user in project.waiting_requested_members:
            flash_warning(lazy_gettext(u'관리자의 승인을 기다리고 있는 사용자입니다.'))
        else:
            request_message = form.request_message.data or u''
            project.request_to_join(
                current_user._get_current_object(), request_message)
            flash_success(lazy_gettext(u'요청되었습니다. 관리자 승인 후 사용 가능합니다.'))

    return redirect(request.args.get('next') or
                    request.referrer or
                    url_for('.index', project_id=project_id))


@bpapp.route('/p/<mbj:project_id>/_delegate_owner', methods=['POST'])
def delegate_owner(project_id):

    form = DelegateProjectOwnerForm(request.form)
    if request.method == 'POST' and form.validate():

        from erks.models import ProjectUser
        user = User.objects.get(email=form.target_user_email.data)
        entry = ProjectUser.objects(project=g.project, user=user).first()
        entry.is_owner = True
        entry.save()

        user = current_user._get_current_object()
        entry = ProjectUser.objects(project=g.project, user=user).first()
        entry.is_owner = False
        entry.save()

        flash_success(gettext(u'소유자 이관이 완료되었습니다.'))
        return redirect(url_for('.index', project_id=project_id))

    else:
        if form.errors.get('target_user_email'):
            flash_error(form.errors['target_user_email'][0])
        else:
            flash_error(gettext(u'소유자 이관이 실패했습니다.'))

        # return redirect_back(url_for('.preference', project_id=project_id))
        return redirect(request.args.get('next') or
                        request.referrer or
                        url_for('.preference', project_id=project_id))


@bpapp.route('/p/<mbj:project_id>/_member_role_action', methods=['POST'])
def member_role_action(project_id):
    from erks.models import ProjectUser, ProjectUserBase
    what = request.form['action']
    if what == 'invite_member':
        user = User.objects.get_or_404(pk=request.form['user_id'])
        if g.project.invite(user.email, current_user._get_current_object()):
            project_user = ProjectUser.objects(
                project=g.project, user=user).get_or_404()
        else:
            project_user = user
    else:
        project_user = ProjectUserBase.objects.get_or_404(
            id=request.form['project_user_id'])

        if what == 'modeler_p':
            project_user.is_modeler = True
            project_user.save()
        elif what == 'termer_p':
            project_user.is_termer = True
            project_user.save()
        elif what == 'modeler_m':
            project_user.is_modeler = False
            project_user.save()
        elif what == 'termer_m':
            project_user.is_termer = False
            project_user.save()
        elif what == 'ban':
            project_user.delete()
            # return '<td>-</td><td colspan="6">{0} 사용자는 더 이상 프로젝트 소속이
            # 아닙니다.</td>'.format(project_user.user)
        elif what == 'approve':
            new_project_user = project_user.approve_and_get_new_project_user()
            if new_project_user:
                project_user = new_project_user
            else:
                # return '<td>-</td><td colspan="6">{0} 프로젝트의 최대 회원수를 초과하여 수락이 불가능합니다.</td>'.format(project_user.user.email)
                # flash_error(lazy_gettext(u'허용된 회원수를 초과하였습니다.'))
                pass
        elif what == 'reject':
            project_user.delete()
        elif what == 'resend':
            project_user.sendmail()
        elif what == 'cancel_invitation':
            project_user.delete()
            # return '<td>-</td><td colspan="6">{0} 사용자의 초대가
            # 취소되었습니다.</td>'.format(project_user.user)

    # return render_template(project_user.render_template_path,
    #                        project=g.project,
    #                        project_user=project_user)
    # import pdb; pdb.set_trace()
    import json
    return jsonify(json.loads(project_user.to_json()))
    # return project_user.to_json()


def _profile_img(project, thumbnail=False):
    try:
        if thumbnail and \
                project.profile_imgf and \
                project.profile_imgf.thumbnail:
            image_binary = project.profile_imgf.thumbnail.read()
        elif project.profile_imgf:
            image_binary = project.profile_imgf.read()
        else:
            image_binary = None
    except IOError:
        image_binary = None

    if image_binary:
        response = make_response(image_binary)
        response.headers['Content-Type'] = gettext(u'image/jpeg')
        content = 'attachment; filename=profile.%s.jpg' % (project.id)
        response.headers['Content-Disposition'] = content
        return response
    else:
        if thumbnail:
            filename = 'img/project_card_default_thumbnail.png'
        else:
            filename = 'img/project_card_default.png'
        return redirect(url_for('static', filename=filename))


@bpapp.route('/profile.<mbj:project_id>.timg')
def profile_timg(project_id):
    return _profile_img(g.project, True)


@bpapp.route('/profile.<mbj:project_id>.img')
def profile_img(project_id):
    return _profile_img(g.project, False)


@bpapp.route('/profile.<mbj:project_id>.img/delete')
def delete_profile_img(project_id):
    project = Project.objects.only('profile_imgf')\
        .no_dereference().get_or_404(id=project_id)
    if project.profile_imgf:
        project.reload()
        project.profile_imgf.delete()
        project.profile_imgf = None
        project.save()
    return redirect(url_for('.preference', project_id=project_id))


# @bpapp.route('/p/<mbj:project_id>/_subscription_log')
# def _subscription_log(project_id):
#     project = g.project
#     log = Order.objects(project=project).order_by('-pay_when')
#     return render_template('project/_preference_billing_log.htm.j2',
#                            project=project, billing_log=log)


# @bpapp.route('/p/<mbj:project_id>/subscription', methods=['GET', 'POST'])
# def subscription(project_id):
#     try:
#         seq = int(request.args.get('seq', 1))
#     except ValueError:
#         seq = 1

#     if seq == 1:
#         form = ProjectSubscriptionForm(request.form)
#     elif request.method == 'POST':
#         form = ProjectSubscriptionFormWizardStepTwo(request.form)

#     return render_template('project/project_subscription.html',
#                            form=form,
#                            seq=seq,
#                            project=g.project)


# @bpapp.route('/p/<mbj:project_id>/_subscription_ksnet_result', methods=['POST'])
# def _subscription_ksnet_result(project_id):

#     # user = current_user._get_current_object()
#     form = ProjectSubscriptionForm(request.form)
#     # project = g.project

#     if request.method == 'POST':
#         try:
#             if form.validate():
#                 project = form.save()
#                 kw = json.loads(form.erks_transaction.data.to_json())
#                 if 'project_group' in kw:
#                     del kw['project_group']
#                 kw['purchased_project'] = project
#                 current_app.logger.debug(kw)
#                 return render_template('billing_result.html', **kw)
#             else:
#                 current_app.logger.warning(form.errors)
#                 return render_template('project/project_subscription.html',
#                                        form=form,
#                                        seq=2,
#                                        project=g.project)
#         except ValidationError:
#             flash_error(gettext(u'결제에 문제가 발생했습니다.'))
#             return redirect(url_for('project.index', project_id=project_id))
#     else:
#         abort(400)


# @bpapp.route('/p/<mbj:project_id>/_cancel_subscription/<mbj:order_id>')
# def cancel_subscription(project_id, order_id):
#     order = Order.objects.get_or_404(id=order_id, project=g.project)
#     order.cancel()

#     return redirect(url_for('project.preference', project_id=project_id))


@bpapp.route('/p/<mbj:project_id>/_leave')
def leave(project_id):
    project = Project.objects.get_or_404(id=project_id)
    if project.leave(current_user._get_current_object()):
        flash(lazy_gettext(u'%(title)s 프로젝트를 탈퇴하셨습니다.', title=project.title))
    return redirect(url_for('portal.index'))


@bpapp.route('/p/<mbj:project_id>/_destroy', methods=['POST'])
def destroy(project_id):
    project = Project.objects.get_or_404(id=project_id)
    form = ProjectDeleteForm(request.form)
    if request.method == 'POST' and form.validate():
        project.destroy()
        flash(lazy_gettext(u'프로젝트가 삭제되었습니다.'))
        # flash(lazy_gettext(u'your project has been removed successfully'))
        return redirect(url_for(
            'project_group.list_projects',
            slug=project.project_group.slug))
    else:
        current_app.logger.warning(form.errors)
        return redirect(url_for(
            'project.preference',
            project_id=project_id))


@bpapp.route('/p/<mbj:project_id>/_members', methods=['GET', 'POST'])
def _members(project_id):
    """project-member-portlet의 내용."""
    from erks.models import ProjectUserBase
    project = g.project
    project_group = project.project_group
    form = SearchMemberForm(project=project)

    if request.method == 'POST':
        search_text = request.form['search_text']
        project_users = []

        if project.project_group.can_search_member:
            # TODO: PROJECT_GROUP에 속한 USER를 USER에서 찾을 수 없는 성능 이슈
            query = ProjectGroupUser.objects(
                project_group=project_group).order_by('-last_visited_at')
            for pgu in query:
                if pgu.user.email.find(search_text) >= 0 or \
                   pgu.user.name.find(search_text) >= 0:
                    pu = ProjectUserBase.objects(
                        project=project,
                        project_group_user=pgu,
                        user=pgu.user).first()
                    if pu:
                        project_users.append(pu)
                    else:
                        project_users.append(pgu.user)
        else:
            pass
    else:
        search_text = ''
        project_users = ProjectUserBase.objects(
            project=project).order_by('-last_visited_at')

    return render_template(
        'project/members.htm.j2',
        project=project,
        project_users=project_users,
        search_form=form,
        search_text=search_text)


# @bpapp.route('/p/<mbj:project_id>/_subscribe', methods=['GET', 'POST'])
# def subscribe(project_id):
#     project = g.project
#     return render_template('project/project_subscribe.html', project=project)


@bpapp.route('/p/<mbj:project_id>/_convert_to_free', methods=['GET', 'POST'])
def convert_to_free(project_id):
    project = g.project

    if not project.is_expired:
        flash_warning(lazy_gettext(u'아직 전환할 수 있는 시기가 아닙니다.'))
    elif project.available_to_convert_free_project():
        project.convert_free_project()
        flash_success(lazy_gettext(
            u'이용해주셔서 감사합니다. '
            u'무료프로젝트로 전환되어 계속 사용하실 수 있습니다.'))
    else:
        flash_error(lazy_gettext(u'이미 무료프로젝트가 존재합니다.'))

    return redirect(url_for('project.index', project_id=project.id))


@bpapp.route('/p/<mbj:project_id>/layout',
             methods=['POST'])
def project_layout(project_id):
    from erks.models import ProjectUser
    pu = ProjectUser.objects(
        project=ObjectId(project_id),
        user=current_user._get_current_object()).first()
    pu.project_layout = request.form.get('what', 'boxed')
    pu.save()
    return jsonify(ret='ok')
