# -*- encoding:utf-8 -*-
from flask_mongoengine.wtf import model_form
from flask_login import current_user
from flask_babel import lazy_gettext, gettext
from wtforms import ValidationError
from wtforms.fields.html5 import EmailField
from erks.utils import password_hash

from .models import User
from erks.utils.form.validators import image_file_validator
import wtforms as wtf
import passwordmeter

from erks.erks_bps.project_group.models import ProjectGroup

pmeter = passwordmeter.Meter(settings=dict(factors='charmix'))


class BaseHtmlMixIn(object):

    def base_html(self):
        project_group = ProjectGroup.objects.get(slug='default')
        if project_group and project_group.has_theme():
            return 'theme/{theme_key}/base_{theme_key}.html'.format(theme_key=project_group.theme_key)
        else:
            return "base.html"

    # def theme_page(self, page):
    #     project_group = ProjectGroup.objects.get(slug='default')
    #     if project_group and project_group.has_theme():
    #         return 'theme/{theme_key}/{page}_{theme_key}.html'.format(page=page, theme_key=project_group.theme_key)
    #     else:
    #         return page + ".html"


class LoginForm(model_form(User, exclude=['created_at', 'user_no', 'user_id', ])):
    email = EmailField('Email', [
        wtf.validators.Length(max=255),
        # wtf.validators.Email(message=None),
    ])
    password = wtf.PasswordField(
        lazy_gettext(u'비밀번호'),
        [
            wtf.validators.Length(min=1),
            wtf.validators.Required(),
        ])
    remember_me = wtf.BooleanField(label=lazy_gettext(u'로그인 상태 유지'))


class SignUpForm(model_form(User, exclude=['created_at', 'user_no', 'user_id', ])):
    email = EmailField('Email', [
        wtf.validators.Length(max=255),
        wtf.validators.Email(message=lazy_gettext(u'올바른 이메일 포맷이 아닙니다.')),
    ])
    password = wtf.PasswordField(
        lazy_gettext(u'비밀번호'),
        [
            wtf.validators.Length(min=8, message=lazy_gettext(u'8자리 이상으로 설정해주세요.')),
            wtf.validators.Required(),
        ])
    password_confirm = wtf.PasswordField(
        lazy_gettext(u'비밀번호 재입력'),
        [
            wtf.validators.Required(),
            wtf.validators.EqualTo(
                'password', message=lazy_gettext(u'비밀번호가 일치해야 합니다.')),
        ])

    def validate_password(form, field):
        score, result = pmeter.test(field.data)
        if len(result) and 'charmix' in result:
            raise ValidationError(lazy_gettext(u'영문, 숫자, 특수문자를 조합하여 설정해주세요.'))


class ChangePasswordForm(BaseHtmlMixIn, model_form(User, only=('password', ))):
    current_password = wtf.PasswordField(
        lazy_gettext(u'현재 비밀번호'),
        [
            wtf.validators.Required(),
        ])
    password = wtf.PasswordField(
        lazy_gettext(u'신규 비밀번호'),
        [
            wtf.validators.Length(min=8, message=lazy_gettext(u'8자리 이상으로 설정해주세요.')),
            wtf.validators.Required(),
        ])
    password_confirm = wtf.PasswordField(
        lazy_gettext(u'신규 비밀번호 재입력'),
        [
            wtf.validators.Required(),
            wtf.validators.EqualTo(
                'password', message=lazy_gettext(u'확인을 위한 신규 비밀번호가 서로 일치하지 않습니다.'))

        ])

    def validate_password(form, field):
        score, result = pmeter.test(field.data)
        if len(result) and 'charmix' in result:
            raise ValidationError(gettext(u"영문, 숫자, 특수문자를 조합하여 설정해주세요."))

    def validate_current_password(form, field):
        user = current_user._get_current_object()
        if user.password != password_hash(field.data):
            raise ValidationError(lazy_gettext(u'입력하신 비밀번호가 현재 비밀번호와 일치하지 않습니다.'))


class ProfileEditForm(model_form(User, only=('name', 'profile', 'default_project_group_id'))):
    name = wtf.TextField(lazy_gettext(u'이름'))
    profile = wtf.TextField(lazy_gettext(u'자기소개'))
    # , [wtf.validators.regexp(ur'^[^/\\]\.jpg$')])
    profile_imgf = wtf.FileField(lazy_gettext(u'이미지 파일'), validators=[image_file_validator('USER_PROFILE_IMAGE_MAX_CONTENT_LENGTH'), ])
    default_project_group_id = wtf.SelectField(lazy_gettext(u'시작프로젝트그룹'))

    def validate_default_project_group_id(form, field):
        if field.data == '':
            field.data = None

    def populate_obj(self, obj):
        """image-data는 평소에는 전달되지 않는데 None을 할당해버리면
        기존 데이타가 지워져버리기 때문에 None이면 아예 처리하지 않기."""

        if self.profile_imgf.data is None:
            setattr(self, '_profile_imgf', self.profile_imgf)
            del self.profile_imgf
            ret = super(ProfileEditForm, self).populate_obj(obj)
            setattr(self, 'profile_imgf', self._profile_imgf)
            del self._profile_imgf
            return ret
        else:
            return super(ProfileEditForm, self).populate_obj(obj)
