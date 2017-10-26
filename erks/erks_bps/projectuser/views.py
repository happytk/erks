# -*- encoding:utf8 -*-
from . import bpapp
from flask import request, render_template, redirect, url_for
from flask_babel import lazy_gettext, gettext
from erks.erks_bps.projectuser.models import ProjectUser
from erks.erks_bps.projectuser.forms import ProjectUserRoleForm
from erks.utils import (
    # flash_error,
    flash_success,
    # flash_warning,
)


@bpapp.route('/pu/<mbj:project_user_id>/_role_changer',
             methods=['GET', 'POST'])
def _user_role_changer(project_user_id):
    pu = ProjectUser.objects.get_or_404(id=project_user_id)
    if request.method == 'POST':
        form = ProjectUserRoleForm(request.form)
        if form.validate():
            # import pdb; pdb.set_trace()
            form.populate_obj(pu)
            pu.save()
            flash_success(lazy_gettext(u'성공적으로 저장되었습니다.'))
    else:
        form = ProjectUserRoleForm(obj=pu)

    return render_template(
        'project/_role_changer.htm.j2',
        form=form,
        project_user=pu)


@bpapp.route('/pu/<mbj:project_user_id>/leave',
             methods=['GET'])
def user_leave(project_user_id):
    pu = ProjectUser.objects.get_or_404(id=project_user_id)
    pu.delete()
    flash_success(gettext(u'%(user_email)s 사용자는 더 이상 프로젝트의 구성원이 아닙니다.', user_email=pu.user_email))
    return redirect(url_for('project.members', project_id=pu.project.id))
