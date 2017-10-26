# -*- encoding:utf-8 -*-
u"""
PROJECT / PROJECT_GROUP / PRODUCT Description.

프로젝트는 사용자가 모여서 협업할 수 있는 기본 공간을 정의합니다.
프로젝트그룹은 프로젝트를 그룹지을 수 있는 공간입니다.
프로젝트와 프로젝트 그룹은 내부적으로 하나의 상품을 갖습니다.
"""
# pylint: disable=E1101, E1120, E501, R0903

import logging as logger
from datetime import datetime, timedelta

from erks.extensions import db
from erks.utils import JsonifyPatchMixin
from erks.erks_bps.login.models import User, UserToken
from erks.erks_bps.project_group.models import ProjectGroupUser
# from erks.erks_bps.glossary.models import GlossaryBase
from erks.tasks import sendmail

import mongoengine
from mongoengine import ValidationError
from flask_babel import lazy_gettext
from flask import (
    render_template,
    url_for,
)


class InviteToken(UserToken):
    """
    PROJECT에서 초청되었을때 생성되는 가입토큰
    """

    project = db.ReferenceField(
        'Project',
        reverse_delete_rule=mongoengine.CASCADE)

    def sendmail(self):
        """project 초청메일 발송(project_url을 발송한다.)
        가입자, 미가입자 상관없이 메일이 발송된다.

        TODO: 미가입자에 대한 안내가 별도로 필요할 수 있음
        """
        signup_url = url_for('login.signup', _external=True)
        title = lazy_gettext(
            u'NEXCORE ER-C 프로젝트에 초대되었습니다.'
            '[%(title)s]', title=self.project.title)
        message = render_template(
            'project/invite.email',
            signup_url=signup_url,
            project=self.project)
        return sendmail(self.email, title, message)

    def is_valid(self, email, project):
        '''project에 속한 email의 invitation의 유효성을 체크합니다.
        7일의 유효기간으로 계산해서 유효여부를 True/False로 리턴.
        '''
        try:
            time_threshold = datetime.now() - timedelta(days=7)
            token = InviteToken.objects.get(
                email=email, project=self, created_at__gte=time_threshold)
            logger.debug('token found(id: %s)' % token.id)
            ret = True
        except InviteToken.DoesNotExist:
            ret = False
        return ret


class ProjectUserBase(JsonifyPatchMixin,
                      db.Document):
    """프로젝트-사용자를 표현하는 기본클래스.
    정확히는 프로젝트와 프로젝트그룹사용자의 관계를 표현한다.
    사용자객체와 email은 자주 꺼내쓰기때문에 cache해둔다.
    """

    meta = {
        'allow_inheritance': True,
        'index_cls': False,
        'indexes': [
            {'fields': ['project', 'user'], 'unique': True},
        ],
    }

    ####################################################################
    # fields
    ####################################################################
    project = db.ReferenceField(
        'Project',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)
    created_at = db.DateTimeField(default=datetime.now)

    ####################################################################
    # cached property
    user_email = db.EmailField(max_length=255)
    user = db.ReferenceField(
        'User',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)
    # end-of-cached property
    ####################################################################

    # def to_json(self, *args, **kwargs):
    #     """기본적인 to_json동작은 mongodb의 bson에 대한 변환이기 때문에
    #     결과물에 encrypted-email이 노출된다. email필드만 별도로 decrypt해서 내보내는
    #     patch-logic을 구현"""
    #     ret = super(ProjectUserBase, self).to_json(*args, **kwargs)

    #     # patch for email-encryption (slow...)
    #     from json import dumps, loads
    #     d = loads(ret)
    #     d['user_email'] = decrypt(d['user_email'])
    #     return dumps(d)


class ProjectUserReportSubscriptionMixin(object):
    subscribed_report_model_glossary = db.BooleanField(default=False)
    subscribed_report_model_schema = db.BooleanField(default=False)
    subscribed_report_model_change = db.BooleanField(default=False)


class ProjectUserReportSubscription(db.Document,
                                    ProjectUserReportSubscriptionMixin):
    '''project-user에 넣으면 좋지만,
    고객사요건으로 project-user가 아닌 경우에도 구독이 가능해야 해서,
    시간과 영향도를 고려하여 불가피하게 별도 collection으로 분리하게 되었음.
    추후 project-user로 편입시킬 수 있으면 좋겠음.'''
    project = db.ReferenceField(
        'Project',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)
    user = db.ReferenceField(
        'User',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)


class ProjectUser(ProjectUserBase,
                  ProjectUserReportSubscriptionMixin):
    """project에 속한 user관리."""

    project_group_user = db.ReferenceField(
        'ProjectGroupUser',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)

    is_owner = db.BooleanField(default=False)
    last_visited_at = db.DateTimeField(default=datetime.now)

    # # for modeling
    # is_modeler = db.BooleanField(default=False)
    # can_manage_all_models = db.BooleanField(default=True)
    # manageable_models = db.ListField(db.ReferenceField(
    #     'Model', reverse_delete_rule=mongoengine.PULL))

    # # for terming
    # is_termer = db.BooleanField(default=False)
    # can_manage_all_glossaries = db.BooleanField(default=True)
    # manageable_glossaries = db.ListField(db.ReferenceField(
    #     'GlossaryBase', reverse_delete_rule=mongoengine.PULL))

    # ui
    project_layout = db.StringField(default='boxed')

    render_template_path = 'project/_members_tbl_row.html'

    def clean(self):
        pgu = ProjectGroupUser.objects(
            project_group=self.project.project_group, user=self.user).first()
        if pgu is None:
            raise ValidationError('Invalid project-group-user-mapping')
        else:
            self.project_group_user = pgu

        # cached property
        self.user_email = self.user.email

    def visit(self):
        if self.project.demo:
            return
        # self.last_visited_at = datetime.now()
        # self.save()
        self.update(last_visited_at=datetime.now())

    @property
    def grades(self):
        ret = []
        if self.is_owner:
            ret.append('owner')
        if self.is_modeler:
            ret.append('modeler')
        if self.is_termer:
            ret.append('termer')
        if len(ret) == 0:
            ret.append('member')
        return ret

    def __unicode__(self):
        return u'%s:%s:%s' % (self.project, self.user, ','.join(self.grades))


class ProjectWaitingUserInbound(ProjectUserBase):

    project_group_user = db.ReferenceField(
        'ProjectGroupUser',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)

    """사용자가 가입요청을 했을 경우"""
    done = db.BooleanField(default=False)
    done_by = db.ReferenceField(
        'User', reverse_delete_rule=mongoengine.NULLIFY)
    done_at = db.DateTimeField(default=datetime.now)
    done_message = db.StringField()
    rejected = db.BooleanField(default=False)

    asked_at = db.DateTimeField(default=datetime.now)
    asked_message = db.StringField()

    render_template_path = 'project/_members_waiting_tbl_row.html'

    def clean(self):
        pgu = ProjectGroupUser.objects(
            project_group=self.project.project_group, user=self.user).first()
        if pgu is None:
            raise ValidationError('Invalid group-project-usermapping')
        else:
            self.project_group_user = pgu

        # cached property
        self.user_email = self.user.email

    def approve_and_get_new_project_user(self):
        if not self.project.is_new_member_available():
            return None

        project = self.project
        user = self.user

        self.delete()

        return ProjectUser(project=project, user=user).save()


class ProjectWaitingUserOutbound(ProjectUserBase):
    """가입되지 않은 사용자를 초대받을때"""
    user = db.EmailField(required=True)
    outbound_email_sent_at = db.DateTimeField()
    outbound_email_sent_count = db.IntField(default=0)
    invited_by = db.ReferenceField(
        'User',
        reverse_delete_rule=mongoengine.NULLIFY)
    invited_at = db.DateTimeField(default=datetime.now)
    # dropped = db.BooleanField(default=False)

    render_template_path = 'project/_members_invited_tbl_row.html'

    @property
    def is_expired(self):
        '''초대요청이 오래지나면 만료된다. 만료기간은 14일.'''
        return self.outbound_email_sent_at < datetime.now() - \
            timedelta(days=14)

    def check_integrity(self):
        '''외부사용자객체의 무결성을 검사합니다.
        외부사용자로 되어있는데 실제 user에도 존재하는 경우는 강제보정
        만료된 객체의 경우 삭제처리합니다.'''

        if self.is_expired:
            logger.info(
                'Deleting expired old-waiting-user-project-relation'
                '[%s].', self)
            self.delete()
        else:
            user = User.objects(email=self.user).first()
            if user:
                '''이미 가입된 사용자로 존재하는군요.
                프로젝트와의 관계까지검사합니다.'''
                relation = ProjectUserBase.objects(
                    project=self.project, user=user).first()
                if relation:
                    logger.info(
                        'Deleting useless old-waiting-user-project-relation'
                        '[%s].', self)
                    self.delete()  # useless.
                else:
                    '''미처리된 사용자이므로 가입처리'''
                    new_project_user = ProjectUser(
                        project=self.project, user=user).save()
                    logger.info('Creating new-user-project-relation'
                                '[%s].', new_project_user)
                    logger.info('Deleting old-waiting-user-project-relation'
                                '[%s].', self)
                    self.delete()
            else:
                '''정상적인 waiting이므로 done nothing.'''
                pass

    def sendmail(self):
        if self.outbound_email_sent_count > 4:
            logger.warning('outbound-email[%s]-surge-protection', self.user)
            return

        token = InviteToken(email=self.user, project=self.project).save()
        token.sendmail()

        self.outbound_email_sent_at = datetime.now()
        self.outbound_email_sent_count += 1
        self.save()

    def clean(self):
        if self.project.project_group.is_not_default:
            raise ValidationError(
                'outbound-user cannot be created at non-default-project-group')

        # 초대그룹의 email이 encrypt되어있지 않아서 다른쪽과 interface를 맞추기 위해 암호화
        self.user_email = self.user

    def to_json(self, *args, **kwargs):
        """일부 계산된 properties를 json으로 내보내기 위한 patch"""
        ret = super(ProjectWaitingUserOutbound, self).to_json(*args, **kwargs)

        # patch for email-encryption (slow...)
        from json import dumps, loads
        d = loads(ret)
        d['is_expired'] = self.is_expired
        return dumps(d)
