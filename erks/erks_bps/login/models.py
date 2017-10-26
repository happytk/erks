# -*- encoding:utf-8 -*-
"""
사용자모델.
python은 순환참조를 스스로 해결할 수 없기 때문에
사용자모델을 project-user관계에서 최상위 모델로 선언한다.
"""

import datetime
import logging as logger

from uuid import uuid4
from flask_babel import lazy_gettext
from flask import url_for, render_template, g

from erks.signals import on_created_user, on_verified_user
from erks.extensions import db
from erks.tasks import sendmail
# from erks.utils.crypt import EncryptedEmailField
from erks.utils import (
    JsonifyPatchMixin,
)


class EmailToken(db.Document):
    meta = {
        'allow_inheritance': True,
    }

    email = db.EmailField(max_length=255, required=True)
    token = db.StringField(
        default=lambda: str(uuid4()).replace('-', ''), required=True)
    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)

    def __unicode__(self):
        return self.email


class UserToken(EmailToken):
    """
    사용자가입확인Token
    """

    def __unicode__(self):
        return self.email

    def is_newest(self):
        token = UserToken.objects(
            email=self.email).order_by('-created_at').first()
        return token.token == self.token

    def _build_url(self):
        return url_for('login.verify', token=self.token, _external=True)

    def sendmail(self):
        title = lazy_gettext(u'[NEXCORE ER-C] 회원가입을 위해 이메일 주소를 확인해주세요.')
        message = render_template(
            'login/invite.email',
            invite_url=self._build_url())
        return sendmail(self.email, title, message)


class PasswordVerifyToken(EmailToken):
    """
    비밀번호리셋토큰
    """

    def __unicode__(self):
        return self.email

    def _build_url(self):
        return url_for(
            'login.password_verify', token=self.token, _external=True)

    def sendmail(self):
        title = lazy_gettext(u'[NEXCORE ER-C]  비밀번호 초기화 메일입니다.')
        message = render_template(
            'login/reset_password.email',
            reset_url=self._build_url())
        return sendmail(self.email, title, message)


class UserProjectGroupMixin(object):
    default_project_group_id = db.ObjectIdField()

    @property
    def default_project_group(self):
        from erks.models import ProjectGroup
        if self.default_project_group_id:
            return ProjectGroup.objects(
                id=self.default_project_group_id).first()
        else:
            return ProjectGroup.default()

    @property
    def queryset_project_group_user(self):
        from erks.erks_bps.project_group.models import ProjectGroupUser
        return ProjectGroupUser.objects(user=self)


class UserProjectMixin(object):

    @property
    def queryset_project(self):
        from erks.models import Project
        return Project.objects(created_by=self)

    @property
    def queryset_project_user(self):
        from erks.models import ProjectUser
        return ProjectUser.objects(user=self)

    @property
    def queryset_project_user_report_subscription(self):
        from erks.models import ProjectUserReportSubscription
        return ProjectUserReportSubscription.objects(user=self)

    @property
    def context_glossary(self):
        from erks.models import ProjectUser, ProjectGroupUser
        pgu = ProjectGroupUser.objects(
            user=self, project_group=g.project_group).first()
        glossaries = []
        for pu in ProjectUser.objects(
                user=self, project_group_user=pgu, is_termer=True):
            if pu.can_manage_all_glossaries:
                glossaries.extend(pu.project.queryset_glossary.all())
            else:
                glossaries.extend(pu.manageable_glossaries)
        return glossaries


class UserProjectCreateBillingCheckMixin(object):

    @property
    def can_make_project(self):
        # from erks.erks_bps.project.models import Project
        # return len(Project.my_free_project()) == 0
        return True

    def can_make_project_for(self, project_group):
        # '''순수하게 billing차원에서만 점검. project_group은 무조건 true'''
        # if project_group.has_theme():
        #     return True
        # elif project_group.is_default:
        #     return self.can_make_project
        # else:
        #     return True
        return True


class UserProfileImageMixin(object):
    profile_imgf = db.ImageField(collection_name='profile_images',
                                 size=(140, 140, True),
                                 thumbnail_size=(35, 35, True),)

    def get_profile_img_tag(self, thumbnail=False):
        url = self.get_profile_img_url(thumbnail)
        return '<img src="%s" class="circle responsive-img"/>' % url

    def get_profile_img_url(self, thumbnail=False):
        if self.profile_imgf:
            if thumbnail:
                return url_for('login.profile_timg', mailaddr=self.email)
            else:
                return url_for('login.profile_img', mailaddr=self.email)
        else:
            if thumbnail:
                return url_for('static', filename='img/profile_thumbnail.jpg')
            else:
                return url_for('static', filename='img/profile.png')


class FlaskLoginMixin(object):
    """ flask-login interface """

    @property
    def is_active(self):
        return True

    def get_id(self):
        """Return the email address to satisfy Flask-Login's requirements."""
        return self.email

    @property
    def is_authenticated(self):
        return self.verified

    @property
    def is_anonymous(self):
        return False


class AdminMixin(object):
    @property
    def is_admin(self):
        return self.admin
    admin = db.BooleanField(default=False)


# class UserNotificationMixin(object):

#     def notifications_cnt(self, is_read=False):
#         if is_read:
#             return UserNotification.objects(user=self).count()
#         else:
#             return UserNotification.objects(user=self, is_read=is_read).count()

#     def notifications(self, limit=None):
#         if limit:
#             return UserNotification.objects.filter(user=self)\
#                 .limit(limit).order_by('-created_at')
#         else:
#             return UserNotification.objects.filter(user=self)\
#                 .order_by('-created_at')

#     def read_user_noti(self, noti_id):
#         try:
#             user_noti = UserNotification.objects.get(id=noti_id)
#             user_noti.is_read = True
#             user_noti.save()
#             # user_noti.delete()
#         except UserNotification.DoesNotExist:
#             pass

#     def read_all_user_noti(self, user_id):
#         UserNotification.objects(user=user_id).update(is_read=True)

#     def notify(self, *args, **kwargs):
#         pass


class UserVerifyMixin(object):
    verified = db.BooleanField(default=False)

    def verify(self):
        if not self.verified:
            self.verified = True
            self.save()
            logger.debug(u'%s is verified' % self)
            on_verified_user.send(self)
        else:
            logger.warning(u'%s is already verified' % self)


class UserLocaleMixin(object):
    locale = db.StringField()


class User(JsonifyPatchMixin,
           db.Document,
           AdminMixin,
           FlaskLoginMixin,
           UserProjectMixin,
           UserProfileImageMixin,
           UserProjectGroupMixin,
           UserProjectCreateBillingCheckMixin,
           UserVerifyMixin,
           UserLocaleMixin):

    meta = {
        'ordering': ['-created_at']
    }

    # email_without_domain = db.StringField(max_length=255)
    email = db.EmailField(max_length=255, required=True, unique=True)
    user_id = db.StringField(max_length=255, unique=True, sparse=True)
    user_no = db.StringField(max_length=255)
    name = db.StringField(max_length=255)
    password = db.StringField(
        max_length=255,
        required=True,
        exclude_to_json=True)
    profile = db.StringField()

    created_at = db.DateTimeField(default=datetime.datetime.now, required=True)

    render_template_path = "project/_user_tbl_row.html"

    # def to_json(self, *args, **kwargs):
    #     """기본적인 to_json동작은 mongodb의 bson에 대한 변환이기 때문에
    #     결과물에 encrypted-email이 노출된다. email필드만 별도로 decrypt해서 내보내는
    #     patch-logic을 구현"""
    #     ret = super(User, self).to_json(*args, **kwargs)

    #     # patch for email-encryption (slow...)
    #     from erks.utils.crypt import decrypt
    #     from json import dumps, loads
    #     d = loads(ret)
    #     d['email'] = decrypt(d['email'])
    #     return dumps(d)

    def resend_verifying_mail(self):
        # TODO: 기존 Token은 삭제하니까 이력추적이 어렵다.
        token = UserToken(email=self.email)
        token.save()
        token.sendmail()

    def clean(self):
        if not self.name:
            try:
                self.name = self.email.split('@')[0]
            except (ValueError, IndexError):
                pass

        # TODO: project_group_id validation

    @property
    def url(self):
        return url_for('.profile')

    def __unicode__(self):
        return self.name or self.email

    def save(self, *args, **kwargs):
        is_new = not self.id
        new_user_obj = super(User, self).save(*args, **kwargs)
        if is_new:
            on_created_user.send(new_user_obj)
            # 신규생성시 verififed를 True로 바로 설정한다면,
            if self.verified:
                on_verified_user.send(new_user_obj)

        return new_user_obj
