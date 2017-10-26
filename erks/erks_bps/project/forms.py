# -*-encoding: utf-8-*-
from flask import url_for, g, current_app
from flask_wtf import FlaskForm as Form
from flask_mongoengine.wtf import model_form
from flask_login import (
    current_user,
)
from flask_babel import lazy_gettext
from datetime import datetime
from dateutil.relativedelta import relativedelta

from wtforms import (
    # Form,
    # TextField,
    # SelectField,
    FileField,
    HiddenField,
    validators,
    BooleanField,
    widgets,
)
from wtforms.validators import ValidationError

# from erks.erks_bps.projectuser.models import (
#     ProjectWaitingUserOutbound, ProjectUser
# )
# from erks.erks_bps.billing.models import Product, Coupon
from erks.erks_bps.project_group.models import ProjectGroup
from erks.erks_bps.project.models import Project
# from erks.erks_bps.glossary.models import Glossary, GlossaryBase
# from erks.erks_bps.erc.models import Model
from erks.utils.form.validators import image_file_validator
from erks.utils.form.fields import ReferenceField
# from erks.erks_bps.billing.forms import (
#     KsNetBillingFormMixIn,
#     ProductBillingMixIn,
# )
from erks.models import User
from flask_babel import gettext

import json
from supports import wtformsparsleyjs

EmailField = wtformsparsleyjs.EmailField
TextField = wtformsparsleyjs.StringField
SelectField = wtformsparsleyjs.SelectField


FIELD_ARGS = {
    'title': {
        'label': lazy_gettext(u'프로젝트 이름'),
    },
    'description': {
        'label': lazy_gettext(u'프로젝트 소개'),
        'widget': widgets.TextArea(),
        'description': lazy_gettext(u'프로젝트를 간단히 표현해주세요.'),
    },
    'private': {
        'label': lazy_gettext(u'프로젝트 비공개'),
        'render_kw': {
            'data-switch-on-text': lazy_gettext(u'<b>프로젝트 회원</b>에게만 공개되며, 허가되지 않은 사용자는 들어올 수 없습니다.'),
            'data-switch-off-text': lazy_gettext(u'프로젝트 멤버 이외의 사용자가 모델과 커뮤니티글을 열람할 수 있는 공개모드입니다.'),
        },
    },
    'visible': {
        'label': lazy_gettext(u'포털 검색에 노출'),
        'render_kw': {
            'data-switch-on-text': lazy_gettext(u'프로젝트가 검색 가능하며 PORTAL화면에 노출될 수 있습니다.'),
            'data-switch-off-text': lazy_gettext(u'프로젝트가 검색에 노출되지 않으며, 초대 혹은 프로젝트 주소 접근으로 사용자 유입이 가능합니다.'),
        },
    },
    'project_group_managed': {
        'label': lazy_gettext(u'관리대상여부'),
        'description': '프로젝트그룹의 프로젝트 중, 대표성을 갖는 대상으로 지정합니다. 그룹내 프로젝트 생성을 누구나 자유롭게 할 경우에는 이 대상을 지정하여 구분관리할 수 있습니다.'
    },
    'contact': {
        'label': lazy_gettext(u'연락처정보'),
        'widget': widgets.TextInput(),
        'description': '포털에 노출되는 연락처 정보입니다. 기본값은 소유자의 이메일입니다.'
    }
}


class ProjectBasicMixin(object):
    title = TextField(
        label=lazy_gettext(u'프로젝트이름'),
        validators=[
            validators.Required(u"프로젝트이름은 필수입력항목입니다."),
            validators.Length(
                min=2, max=40, message=lazy_gettext(u'2-40자 길이로 가능합니다.'))],
        render_kw=dict(placeholder=u"프로젝트 이름(2~40자)"))
    description = TextField(
        label=lazy_gettext(u'프로젝트 소개'),
        render_kw=dict(placeholder=lazy_gettext(u'프로젝트에 대한 설명')))
    project_group = ReferenceField(
        label=lazy_gettext(u'프로젝트 그룹'), model=ProjectGroup)


class ProjectSubscribeForm(Form):

    subscribed_report_model_change = BooleanField(
        gettext(u'모델변경리포트'),
        render_kw={
            'data-label-text': gettext(u'구독'),
        })
    subscribed_report_model_glossary = BooleanField(
        gettext(u'모델용어리포트'),
        render_kw={
            'data-label-text': gettext(u'구독'),
        })
    subscribed_report_model_schema = BooleanField(
        gettext(u'모델스키마리포트'),
        render_kw={
            'data-label-text': gettext(u'구독'),
        })



class ProjectCreateForm(
        ProjectBasicMixin,
        model_form(
            Project,
            only=('title', 'description'),
            field_args=FIELD_ARGS)):
    pass


class ProjectPlusCreateForm(
        ProjectBasicMixin,
        model_form(
            Project,
            only=('title', 'description', 'private', 'visible'),
            field_args=FIELD_ARGS),
        # KsNetBillingFormMixIn,
        # ProductBillingMixIn
        ):

    def __init__(self, *args, **kwargs):
        ret = super(ProjectPlusCreateForm, self).__init__(*args, **kwargs)

        prod = Product.objects(product_code='project_10').first()

        self.sndPaymethod.choices = current_app.config['BILLING_PAY_METHOD_CHOICES']
        self.sndStoreid.data = current_app.config['BILLING_KSNET_STORE_ID']
        self.sndOrdernumber.data = prod.product_code
        self.sndGoodname.data = prod.product_name
        self.unit_price.data = prod.price
        self.product_obj.data = prod

        # read_only(self.sndAmount)
        self.sndEmail.data = current_user.email
        self.sndReply.data = url_for(
            'portal._project_billing_ksnet_rcv', _external=True)
        self.sndResult.data = url_for(
            'project.create_project_plus_result', _external=True)
        # self.sndServicePeriod.data = 지금부터 언제까지
        return ret

    def validate(self):
        '''validate를 항목별로 나누지 않은 이유는 check_by_webhost부터 반드시 call해야하기 때문'''
        try:
            self.check_by_webhost()

            subscription_months = self.subscription_months.data
            erks_transaction_quantity = self.erks_transaction_quantity.data

            current_app.logger.debug(
                subscription_months,
                erks_transaction_quantity)

            if int(subscription_months) != int(erks_transaction_quantity):
                raise ValidationError('invalid-product-quantity-integrity')

            if self.erks_transaction_product.data != self.product_obj.data:
                raise ValidationError('invalid-product-integrity')

        except ValidationError:
            current_app.logger.critical('validation-error', exc_info=True)
            # return ValidationError
            raise ValidationError('invalid-transaction')

        return super(ProjectPlusCreateForm, self).validate()

    def save(self):

        # # project = super(ProjectPlusCreateForm, self).save(commit=False)
        project = Project()
        # project.title = self.title.data
        # project.description = self.description.data
        # project.private = self.private.data
        # project.visible = self.visible.data
        # project.project_group = ProjectGroup.default()

        self.populate_obj(project)

        # import pdb; pdb.set_trace()
        # project.save()
        project.convert_paid_project()

        self.write_project_order(project, self.erks_transaction.data)

        return project


class ProjectPlusCreateFormWizardTwoStep(ProjectPlusCreateForm):
    u"""과금 form 이후 단계에서는 아래 필드들은 보여주지 않는다. 혹은 readonly"""
    title = HiddenField()
    description = HiddenField()
    private = HiddenField()
    visible = HiddenField()
    subscription_months = HiddenField()

    def __init__(self, *args, **kwargs):
        ret = super(ProjectPlusCreateFormWizardTwoStep, self).__init__(*args, **kwargs)

        try:
            months = int(self.subscription_months.data)
        except ValueError:
            months = 1
            self.subscription_months.data = months

        self.sndAmount.data = self.product_obj.data.price * months

        # calculate "service-period"
        service_period_start = datetime.now()
        service_period_end = service_period_start + relativedelta(months=months)
        self.sndServicePeriod.data = "{0}-{1}".format(
            service_period_start.strftime("%Y%m%d"),
            service_period_end.strftime("%Y%m%d"))

        return ret


class ProjectSubscriptionForm(ProjectPlusCreateForm):
    """
    프로젝트내에서 결제를 추가하는 경우에 사용합니다.
    """

    def __init__(self, *args, **kwargs):
        ret = super(ProjectSubscriptionForm, self).__init__(*args, **kwargs)
        del self.title
        del self.description
        # self.sndReply.data = url_for('portal._project_billing_ksnet_rcv', project_id=g.project.id, _external=True)
        # self.sndResult.data = url_for('project._subscription_ksnet_result', project_id=g.project.id, _external=True)
        return ret

    def save(self):
        project = g.project
        project.convert_paid_project()
        self.write_project_order(project, self.erks_transaction.data)
        return project


class ProjectSubscriptionFormWizardStepTwo(ProjectPlusCreateFormWizardTwoStep):

    def __init__(self, *args, **kwargs):
        ret = super(ProjectSubscriptionFormWizardStepTwo, self)\
            .__init__(*args, **kwargs)

        months = int(self.subscription_months.data)

        # calculate "service-period"
        service_period_start, service_period_end = \
            g.project.calculate_subscription_period(months)

        self.sndServicePeriod.data = "{0}-{1}".format(
            service_period_start.strftime("%Y%m%d"),
            service_period_end.strftime("%Y%m%d"))

        self.sndResult.data = url_for(
            'project._subscription_ksnet_result',
            project_id=g.project.id,
            _external=True)

        return ret


# class ProjectPlusCouponCreateForm(
#         ProjectBasicMixin,
#         model_form(
#             Project,
#             only=('title', 'description', 'private', 'visible', ),
#             field_args=FIELD_ARGS),
#         # ProductBillingMixIn
#         ):
#     subscription_months = HiddenField()
#     coupon = ReferenceField(model=Coupon)
#     sndAmount = HiddenField()

#     def __init__(self, *args, **kwargs):
#         ret = super(
#             ProjectPlusCouponCreateForm, self).__init__(*args, **kwargs)
#         if self.coupon.data:
#             coupon = self.coupon.data
#         else:
#             coupon = kwargs.get('coupon')
#             if coupon is None:
#                 raise Exception(
#                     'ProjectPlusCouponCreateForm needs coupon object.')
#         self.product_code.data = coupon.product.product_code
#         self.product_obj.data = coupon.product
#         self.subscription_months.data = coupon.quantity
#         self.unit_price.data = 0
#         self.sndAmount.data = 0
#         return ret

#     def validate_coupon(self, field):
#         if self.coupon.data.used:
#             raise ValidationError(lazy_gettext(u'이미 사용된 쿠폰입니다.'))

#     def save(self):
#         coupon = self.coupon.data
#         self.product_obj.data = coupon.product
#         self.subscription_months.data = coupon.quantity
#         self.sndAmount.data = 0

#         project = Project()
#         self.populate_obj(project)
#         project.convert_paid_project()

#         self.write_project_order(project, coupon)

#         coupon.used = True
#         coupon.used_at = project
#         coupon.used_by = current_user._get_current_object()
#         coupon.used_when = datetime.now()
#         coupon.save()
#         return project


class ProjectEditForm(
        ProjectBasicMixin,
        model_form(
            Project,
            only=('title', 'description', 'contact', 'private', 'visible',),
            field_args=FIELD_ARGS)):
    profile_imgf = FileField(
        lazy_gettext(u'대표 이미지'),
        validators=[
            image_file_validator('PROJECT_BRAND_IMAGE_MAX_CONTENT_LENGTH'),
        ])

    def populate_obj(self, obj):
        """image-data는 평소에는 전달되지 않는데 None을 할당해버리면
        기존 데이타가 지워져버리기 때문에 None이면 아예 처리하지 않기."""
        if self.profile_imgf.data is None:
            setattr(self, '_profile_imgf', self.profile_imgf)
            del self.profile_imgf
            ret = super(ProjectEditForm, self).populate_obj(obj)
            setattr(self, 'profile_imgf', self._profile_imgf)
            del self._profile_imgf
            return ret
        else:
            return super(ProjectEditForm, self).populate_obj(obj)


class ProjectEditForProjectGroupForm(
        ProjectBasicMixin,
        model_form(
            Project,
            only=(
                'title', 'description', 'private', 'visible',
                'project_group_managed'),
            field_args=FIELD_ARGS)):
    pass

# class ProjectSearchForm(Form):
#     """ 프로젝트 검색 """
#     search_string = TextField(label='')


class InviteMemberForm(Form):
    """PROJECT내 멤버초대FORM"""
    emails = TextField(
        "Email", [validators.Required(lazy_gettext(
            u"이메일 주소를 1개 이상 입력해 주세요.."))])

    def clean_emails(self):
        # 중복과 빈 라인을 제거하고 strip.
        receivers = list(set(filter(lambda x: len(x), map(
            lambda x: x.strip(), self.emails.data.split()))))
        return receivers

    def count_invitations(self):
        return len(self.clean_emails())

    def review_invitations(self):

        from erks.erks_bps.projectuser.models import (
            ProjectWaitingUserOutbound
        )

        project = g.project
        project_group = g.project_group

        receivers = [{
            'user_email': email,
            'user': User.objects(email=email, verified=True).first(),
            'is_user': False,
            'is_project_member': False,  # default
            'is_project_group_member': False,  # default
            'ok': False,  # default
            'status_message': '',  # default
        } for email in self.clean_emails()]

        # project-group-member-check
        for r in receivers:
            r['is_user'] = r['user'] is not None

            if r['is_user']:
                # inbound check
                is_pgu = project_group.queryset_member.filter(
                    user=r['user']).first() is not None
                r['is_project_group_member'] = is_pgu

                is_pu = project.queryset_member.filter(
                    user=r['user']).first() is not None
                r['is_project_member'] = is_pu
            else:
                # oubound check if the user is already invited.
                project_user = ProjectWaitingUserOutbound.objects(
                    user=r['user_email'],
                    project=project).first()
                r['is_project_member'] = project_user is not None

            if (r['is_user'] and
                    r['is_project_group_member'] and
                    not r['is_project_member']):
                r['ok'] = True
                msg, status = '초대 가능한 사용자입니다.', 'success'  # ok
            else:
                if not r['is_user']:
                    if r['is_project_member']:
                        msg, status = gettext('이미 초대중인 사용자입니다.'), 'success'
                    else:
                        if project_group.can_invite_oubound_user:
                            r['ok'] = True
                            msg, status = gettext(
                                'ER-C 가입 사용자가 아닙니다. '
                                '외부사용자에게 초대 EMAIL이 발송됩니다.'), 'warning'
                        else:
                            msg, status = gettext(
                                'ER-C 가입 사용자가 아니어서, '
                                '초대가 불가능합니다.'), 'danger'
                elif not r['is_project_group_member']:
                    msg, status = gettext(
                        'ER-C사용자이지만, '
                        '프로젝트 그룹 소속이 아닙니다.'), 'danger'
                elif r['is_project_member']:
                    msg, status = gettext('이미 프로젝트 사용자입니다.'), 'info'
                else:
                    msg, status = gettext('알 수 없는 사용자입니다.'), 'danger'

            r['status_message'] = msg
            r['status'] = status
            if r['user']:
                r['user'] = json.loads(r['user'].to_json())

        return receivers


class SearchMemberForm(Form):
    """PROJECT내 멤버검색FORM"""
    search_text = TextField(gettext("사용자검색"))
    is_owner = BooleanField(
        gettext(u'프로젝트관리자'),
        render_kw={
            'data-label-text': gettext(u'프로젝트관리자'),
        })
    is_termer = BooleanField(
        gettext(u'용어관리자'),
        render_kw={
            'data-label-text': gettext(u'용어관리자'),
        })
    is_modeler = BooleanField(
        gettext(u'모델러'),
        render_kw={
            'data-label-text': gettext(u'모델러'),
        })
    is_member = BooleanField(
        gettext(u'프로젝트멤버'),
        default=True,
        render_kw={
            'data-label-text': gettext(u'프로젝트멤버'),
        })
    is_outbound_user = BooleanField(
        gettext(u'외부사용자초대'),
        render_kw={
            'data-label-text': gettext(u'외부초대사용자'),
        })
    is_inbound_user_request = BooleanField(
        gettext(u'가입요청사용자'),
        render_kw={
            'data-label-text': gettext(u'가입요청사용자'),
        })

    def search(self):
        # q = dict(project=g.project.id, glossary=g.glossary.id)
        q = {}
        if self.search_text.data:
            q['user_email__icontains'] = self.search_text.data
        if self.is_owner.data:
            q['is_owner'] = True
        if self.is_termer.data:
            q['is_termer'] = True
        if self.is_modeler.data:
            q['is_modeler'] = True
        if any([self.is_member.data,
                self.is_outbound_user.data,
                self.is_inbound_user_request.data]):
            lst = []
            if self.is_member.data:
                lst.append('ProjectUserBase.ProjectUser')
            if self.is_outbound_user.data:
                lst.append('ProjectUserBase.ProjectWaitingUserOutbound')
            if self.is_inbound_user_request.data:
                lst.append('ProjectUserBase.ProjectWaitingUserInbound')
            q['_cls'] = {'$in': lst}
        return q

    def __init__(self, *args, **kwargs):
        ret = super().__init__(*args, **kwargs)
        project = kwargs.get('project', None)
        if project:
            cnt = project.queryset_project_user(
                _cls='ProjectUserBase.ProjectWaitingUserInbound', done=False).count()
            if cnt:
                # import pdb; pdb.set_trace()
                self.is_inbound_user_request.label.text = (
                    '<u>가입요청사용자</u> '
                    '<span class="badge badge-danger">'
                    f'{cnt}'
                    '</span>'
                )
        return ret


class RequestMemberForm(Form):
    """PROJECT내 멤버메세지알림FORM - 관리자지정"""
    request_message = TextField("request_message")


class ProjectDeleteForm(Form):
    """PROJECT 삭제FORM."""
    title_matched = TextField(
        lazy_gettext(u"최종 확인을 위해 프로젝트 이름을 입력해 주세요.").upper(),
        # Please type in the name of the project to confirm.
        [
            # Please enter your project title exactly.
            validators.Required(
                lazy_gettext(u"프로젝트 이름을 정확히 입력해 주세요.")),
            validators.EqualTo(
                'title',
                message=lazy_gettext(u'프로젝트 이름이 일치해야 합니다.')),
        ]
    )
    title = HiddenField()


class DelegateProjectOwnerForm(Form):
    """project소유자 이전"""
    target_user_email = EmailField(
        "Email", [validators.Required(gettext(u'이메일 주소를 입력해 주세요..'))])

    def validate_target_user_email(self, field):
        try:
            user = User.objects.get(email=field.data)
        except User.DoesNotExist:
            raise ValidationError(gettext(u'유효한 사용자가 아닙니다.'))

        if g.project and user in g.project.members:
            pass
        else:
            raise ValidationError(gettext(u'프로젝트 구성원이 아닙니다.'))

        if g.project and g.project.owner == user:
            raise ValidationError(gettext(u'이미 관리자입니다.'))
