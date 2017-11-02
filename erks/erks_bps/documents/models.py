# -*- encoding:utf-8 -*-
u"""
PROJECT / PROJECT_GROUP / PRODUCT Description.

프로젝트는 사용자가 모여서 협업할 수 있는 기본 공간을 정의합니다.
프로젝트그룹은 프로젝트를 그룹지을 수 있는 공간입니다.
프로젝트와 프로젝트 그룹은 내부적으로 하나의 상품을 갖습니다.
"""
# pylint: disable=E1101, E1120, E501, R0903

import random
import hashlib
import logging as logger
from datetime import datetime

from erks.extensions import db
from erks.signals import on_created_project, on_changed_project
from erks.utils import JsonifyPatchMixin, AuditableMixin
from erks.erks_bps.login.models import User
# from erks.erks_bps.billing.models import BillingMixin
from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser, THEME_KEYS

from mongoengine import NotUniqueError
from mongoengine.queryset import Q

from flask_login import current_user
from flask import (
    url_for,
    current_app,
)
from flask_babel import gettext
from erks.utils import html_unescape

class documents_sets(db.DynamicDocument):
    meta = {'collection': 'documents_sets'}

class documents(db.DynamicDocument):
    meta = {'collection': 'documents'}

class ground_truth(db.DynamicDocument):
    meta = {'collection': 'ground_truth'}


documents_sets_collection = documents_sets._get_collection()
documents_collection = documents._get_collection()
ground_truth_collection = ground_truth._get_collection()
