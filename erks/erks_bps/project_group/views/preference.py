# -*- encoding:utf8 -*-
from flask import render_template, request, current_app, g
from flask_babel import lazy_gettext, gettext

from erks.utils import flash_success, flash_error
from erks.utils.portlet import Portlet
from erks.errors import (
    ProjectGroupIntegrityError,
)
from erks.erks_bps.project_group import bpapp
from erks.erks_bps.project_group.models import (
    ProjectGroup,
)
from erks.erks_bps.project_group.forms import (
    ProjectGroupForm,
    ProjectGroupMemberPrefForm,
    ProjectGroupSecurityPrefForm,
    ProjectGroupProjectPrefForm,
    # ProjectGroupGlossaryForm,
)


@bpapp.route('/pg/<slug>/conf', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/conf/basic', methods=['GET', 'POST'])
def preference(slug):
    portlets = [
        Portlet('project_group._preference_basic', slug=slug),
    ]
    if current_app.config['BILLING']:
        portlets.append(
            Portlet('project_group._pg_subscription_log', slug=slug))
    return render_template(
        'project_group/preference_portlets.htm.j2',
        active_page='index',
        portlets=portlets
    )


@bpapp.route('/pg/<slug>/conf/_basic', methods=['GET', 'POST'])
def _preference_basic(slug):

    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if request.method == 'POST':
        # import pdb; pdb.set_trace()
        form = ProjectGroupForm(request.form)
        if form.validate():
            form.populate_obj(project_group)
            from erks.models import GlossaryDerived, Glossary
            if form.use_glossary_master.data:
                try:
                    project_group.create_glossary_master()
                    flash_success(gettext(u'마스터 용어집이 생성되었습니다.'))
                except ProjectGroupIntegrityError:
                    pass
                GlossaryDerived.objects(project_group=project_group).update(set__is_active=True)
                Glossary.objects(project_group=project_group).update(set__is_active=False)
            else:
                GlossaryDerived.objects(project_group=project_group).update(set__is_active=False)
                Glossary.objects(project_group=project_group).update(set__is_active=True)
            project_group.save()
            flash_success(gettext(u'설정이 저장되었습니다.'))
        else:
            flash_error(gettext(u'설정폼 정보에 문제가 있습니다.'))
    else:
        form = ProjectGroupForm(obj=project_group)

    d = {}
    d['project_group'] = project_group
    d['form'] = form
    return render_template(
        'project_group/_preference_basic.htm.j2', **d)


@bpapp.route('/pg/<slug>/conf/glossaries', methods=['GET'])
def preference_glossaries(slug):
    return render_template(
        'project_group/preference_portlets.htm.j2',
        active_page='glossaries',
        portlets=[
            Portlet(
                'project_group._preference_glossaries',
                slug=slug),
        ]
    )


@bpapp.route('/pg/<slug>/conf/_glossaries_list', methods=['GET', ])
def _preference_glossaries(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template(
        'project_group/_preference_glossaries.htm.j2',
        project_group=project_group)


@bpapp.route('/pg/<slug>/conf/projects', methods=['GET'])
def preference_projects(slug):
    return render_template(
        'project_group/preference_portlets.htm.j2',
        active_page='projects',
        portlets=[
            Portlet(
                'project_group._preference_project', slug=slug),
            Portlet(
                'project_group._preference_projects', slug=slug),
        ]
    )


@bpapp.route('/pg/<slug>/conf/_project', methods=['GET', 'POST'])
def _preference_project(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)

    if request.method == 'POST':
        form = ProjectGroupProjectPrefForm(request.form)
        if form.validate():
            form.populate_obj(project_group)
            project_group.save()
            flash_success(lazy_gettext(u'설정이 저장되었습니다.'))

            # clean object로 다시 mapping
            form = ProjectGroupProjectPrefForm(obj=project_group)
    else:
        form = ProjectGroupProjectPrefForm(obj=project_group)

    d = {}
    d['project_group'] = project_group
    d['form'] = ProjectGroupProjectPrefForm(obj=project_group)
    return render_template('project_group/_preference_project.htm.j2', **d)


@bpapp.route('/pg/<slug>/conf/_projects_list', methods=['GET', ])
def _preference_projects(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)

    d = {}
    d['project_group'] = project_group
    d['projects'] = project_group.queryset_project
    return render_template(
        'project_group/_preference_projects.htm.j2', **d)


@bpapp.route('/pg/<slug>/conf/members_autoinvite', methods=['GET', 'POST'])
def preference_join_rules(slug):
    return render_template(
        'project_group/preference_portlets.htm.j2',
        active_page='member_join_rules',
        portlets=[
            Portlet(
                'project_group._preference_members_autoinvite',
                slug=slug
            ),
        ]
    )


@bpapp.route('/pg/<slug>/conf/_members_autoinvite', methods=['GET', 'POST'])
def _preference_members_autoinvite(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if request.method == 'POST':
        form = ProjectGroupMemberPrefForm(request.form)
        if form.validate():
            form.populate_obj(project_group)
            project_group.save()
            flash_success(lazy_gettext(u'설정이 저장되었습니다.'))

            # clean object로 다시 mapping
            form = ProjectGroupMemberPrefForm(obj=project_group)
    else:
        form = ProjectGroupMemberPrefForm(obj=project_group)

    d = {}
    d['project_group'] = project_group
    d['form'] = form
    return render_template(
        'project_group/_preference_members_autoinvite.htm.j2', **d)


@bpapp.route('/pg/<slug>/conf/members', methods=['GET', 'POST'])
def preference_members(slug):
    d = {}
    d['project_group'] = g.project_group
    return render_template('project_group/preference_members.html', **d)


@bpapp.route('/pg/<slug>/conf/_members', methods=['GET'])
def _preference_members(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template(
        'project_group/_preference_members.htm.j2',
        project_group=project_group)


@bpapp.route('/pg/<slug>/conf/security', methods=['GET', 'POST'])
def preference_security(slug):
    return render_template(
        'project_group/preference_portlets.htm.j2',
        active_page='security',
        portlets=[
            Portlet(
                'project_group._preference_security',
                slug=slug
            ),
        ]
    )


@bpapp.route('/pg/<slug>/conf/_security', methods=['GET', 'POST'])
def _preference_security(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if request.method == 'POST':
        form = ProjectGroupSecurityPrefForm(request.form)
        if form.validate():
            form.populate_obj(project_group)
            project_group.save()
            flash_success(lazy_gettext(u'설정이 저장되었습니다'))

            # clean object로 다시 mapping
            form = ProjectGroupSecurityPrefForm(obj=project_group)
        else:
            pass
    else:
        form = ProjectGroupSecurityPrefForm(obj=project_group)
    d = {}
    d['project_group'] = project_group
    d['form'] = form
    if request.remote_addr:
        form.use_firewall.description += lazy_gettext(
            u'<br/>'
            u'현재 접속자IP는 '
            u'<span class="bold">%(remote_addr)s</span>입니다.',
            remote_addr=request.remote_addr)
    return render_template(
        'project_group/_preference_security_body.htm.j2', **d)
