# -*-encoding:utf-8-*-

import logging as logger
from flask import current_app
from mongoengine import NotUniqueError
from erks.signals import on_verified_user
from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser


def auto_signup(user):
    """project_group의 가입조건에 맞다면 자동으로 가입처리"""
    logger.debug(f'{user} join-test to project group')
    for pg in ProjectGroup.objects.all():
        if pg.test_joinrule(user.email):
            logger.debug(f'{user} joined to project_group[{pg.slug}] by autosignup')
            ProjectGroupUser(user=user, project_group=pg).save()


def add_to_default_project_group(user):
    """모든 사용자는 생성과 동시에 default_project_group에 가입"""
    try:
        logger.debug(f'{user} joined to default_group')
        project_group = ProjectGroup.objects.get(slug='default')
        ProjectGroupUser(user=user, project_group=project_group).save()
    except NotUniqueError:
        logger.info(f'{user} already joined to default_group')


def add_to_default_config_project_group(user):
    if current_app.config['DEFAULT_PROJECT_GROUP_SLUG'] != 'default':
        slug = current_app.config['DEFAULT_PROJECT_GROUP_SLUG']
        project_group = ProjectGroup.objects.get(slug=slug)
        try:
            logger.debug(f'{user} joined to default_config_group[{slug}]')
            ProjectGroupUser(user=user, project_group=project_group).save()
        except NotUniqueError:
            logger.debug(f'{user} already joined to default_config_group[{slug}]')
    else:
        logger.debug(f'{user} skipped to default_config_group')


on_verified_user.connect(auto_signup)
on_verified_user.connect(add_to_default_project_group)
on_verified_user.connect(add_to_default_config_project_group)
