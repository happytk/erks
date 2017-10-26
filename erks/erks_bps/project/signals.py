# -*-encoding:utf-8-*-

import logging as logger
from erks.signals import on_created_project_group, on_created_project, on_joined_to_project_group
from erks.erks_bps.project_group.models import ProjectGroupUser
from flask_login import current_user


def join_project(*args):
    """
    가입과 동시에 초대된 프로젝트 자동등록.
    프로젝트그룹에 join되었을때 판단해야 한다.
    """
    user, project_group = args[0]
    logger.debug('finding user(%s)-project-join history in %s', user, project_group)
    from erks.models import ProjectWaitingUserOutbound
    for entry in ProjectWaitingUserOutbound.objects(user=user.email):
        if entry.project.project_group.id == project_group.id:
            entry.check_integrity()


on_joined_to_project_group.connect(join_project)
# on_verified_user.connect(join_project)


def make_to_owner(project):
    from erks.models import ProjectUser
    if current_user and current_user.is_active:
        logger.debug('project_group_is_created and current_user_is_adding.')
        ProjectUser(project=project, user=current_user._get_current_object(), is_owner=True).save()
    else:
        logger.warning('Not in the active-context, so cannot map the owner-project[%s]', project)


on_created_project.connect(make_to_owner)


def join_current_user_to_project_group(project_group):
    if current_user and current_user.is_active:
        logger.debug('project_group_is_created and current_user_is_added.')
        ProjectGroupUser(project_group=project_group,
                         user=current_user._get_current_object(),
                         is_owner=True,
                         is_moderator=True).save()
    else:
        user = current_user._get_current_object()
        logger.warning(
            f'project_group_is_created, '
            f'but current_user_is_not_added. - {user}')


on_created_project_group.connect(join_current_user_to_project_group)
