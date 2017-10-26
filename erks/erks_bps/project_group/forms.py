# -*- encoding: utf-8-*-
from flask_mongoengine.wtf import model_form
from flask_mongoengine.wtf.fields import ModelSelectField
from flask_wtf import FlaskForm as Form
from wtforms import (
    # TextField,
    HiddenField,
    FileField,
    FormField,
    validators,
    widgets,
    FieldList,
    # BooleanField,
)
from flask import url_for, g
from wtforms.validators import ValidationError
from erks.utils.form.fields import (
    ReferenceField,
    # QuerySetSelectField,
)
from erks.utils.form.validators import image_file_validator
from erks.utils import flash_warning
from erks.erks_bps.project_group.models import (
    ProjectGroup,
    ProjectGroupNotice,
    FirewallRule,
    ProjectGroupUser
)
# from erks.erks_bps.billing.models import Product
# from erks.erks_bps.billing.forms import (
#     KsNetBillingFormMixIn,
#     ProductBillingMixIn
# )
from erks.erks_bps.login.models import User
from wtforms.widgets import HTMLString
from flask import request, current_app
# from erks.erks_bps.login.models import User
from flask_login import current_user
from flask_babel import lazy_gettext, gettext

import wtforms as wtf
import json
import mongoengine
from supports import wtformsparsleyjs

EmailField = wtformsparsleyjs.EmailField
TextField = wtformsparsleyjs.StringField
SelectField = wtformsparsleyjs.SelectField
BooleanField = wtformsparsleyjs.BooleanField


PG_CREATEGROUP_FIELD_ARGS = {
    'title': {
        'label': lazy_gettext(u'프로젝트 그룹 명'),
        'validators': [
            wtf.validators.Required(
                message=lazy_gettext(u'프로젝트 그룹명을 입력해 주세요.')),
        ]
    },
    'slug': {
        'label': lazy_gettext(u'프로젝트 그룹 ID'),
        'description': lazy_gettext(u'프로젝트 그룹을 식별할 수 있는 URI 주소입니다.') +
        u'''
<span id="project_group_new_slug"
      style="font-weight:bold; color:blue; text-decoration:underline;"></span>
<script type="text/javascript">
$(document).ready(function() {
    var $form = $('#pg_create_form');
    var protocol = location.protocol;
    var port = location.port;
    var hostname = location.host;
    // loc = loc.substring(0, loc.indexof('/'));
    var onchange = function() {
        $('#project_group_new_slug').text(protocol + '//' + hostname + '/pg/' + $(this).val());
    };
    // http://stackoverflow.com/questions/574941/best-way-to-track-onchange-as-you-type-in-input-type-text
    $('#slug', $form).on('keyup', onchange);
});
</script>
''',
        'validators': [
            wtf.validators.Required(
                message=lazy_gettext(u'프로젝트 그룹 ID를 입력해 주세요.')),
        ]
    },
    'description': {
        'label': lazy_gettext(u'소개'),
        'widget': widgets.TextArea(),
        'description': lazy_gettext(u'그룹에 대해서 상세히 표현해주세요.'),
    },
    'private': {
        'label': u'private',
    },
    'visible': {
        'label': u'visible',
    },
}


class ProjectGroupBasicMixin(object):
    title = TextField(
        label=lazy_gettext(u'프로젝트 그룹 이름'),
        validators=[
            wtf.validators.Required(lazy_gettext(u'프로젝트이름은 필수입력항목입니다.')),
            wtf.validators.Length(
                min=2,
                max=40,
                message=lazy_gettext(u'2-40자 길이로 가능합니다.'))
        ],
        render_kw=dict(placeholder=lazy_gettext(u"프로젝트 이름(2~40자)"))
    )
    description = TextField(
        label=lazy_gettext(u'프로젝트 그룹 소개'),
        validators=[
            wtf.validators.Required(lazy_gettext(u"그룹 소개는 필수입력항목입니다.")),
        ],
        render_kw=dict(placeholder=lazy_gettext(u"프로젝트에 대한 설명"))
    )


class ProjectGroupSlugMixin(object):
    slug = TextField(
        label=lazy_gettext(u'프로젝트 그룹 ID'),
        validators=[
            wtf.validators.Required(u"ID는 필수입력항목입니다."),
            wtf.validators.Length(
                min=2,
                max=40,
                message=lazy_gettext(u'2-40자 길이로 가능합니다.'))
        ],
        render_kw={
            'placeholder': u"프로젝트 그룹을 식별할 수 있는 URI 주소입니다.",
            'pattern': '[\da-z\-]+',
            'data-parsley-pattern': '[\da-z\-]+',
            'data-parsley-pattern-message': lazy_gettext(
                u'소문자영어와 숫자, -의 조합만 가능합니다.'),
            'data-parsley-required': "true",
            'data-parsley-required-message': lazy_gettext(u'ID는 필수항목입니다.'),
            'data-parsley-length': "[6, 10]",
            'data-parsley-length-message': lazy_gettext(u'2-40자 길이로 가능합니다.'),
            'data-parsley-remote': '/pg/validate_pg_slug?slug={value}',
            'data-parsley-remote-message': lazy_gettext(u'이미 사용중인 id입니다.'),
            'data-parsley-remote-reverse': "true",
        },
        description='''
<span id="project_group_new_slug"
      style="color:blue; text-decoration:underline;"></span>
<script>
$(document).ready(function() {
    var $form = $('#pg_create_form');
    var protocol = location.protocol;
    var port = location.port;
    var hostname = location.host;
    // loc = loc.substring(0, loc.indexof('/'));
    var onchange = function() {
        $('#slug').parsley().validate();
        $('#project_group_new_slug').text(protocol + '//' + hostname + '/pg/' + $(this).val());
    };
    // http://stackoverflow.com/questions/574941/best-way-to-track-onchange-as-you-type-in-input-type-text
    $('#slug', $form).on('keyup', onchange);
});
</script>'''
    )


class ProjectGroupCreateForm(
    ProjectGroupBasicMixin,
    ProjectGroupSlugMixin,
    model_form(
        ProjectGroup,
        only=(
            'title',
            'slug',
            'description',
            'private',
            'visible'
        ),
        field_args=PG_CREATEGROUP_FIELD_ARGS)):
    pass


class ProjectGroupCreateBillingForm(ProjectGroupCreateForm,
                                    # KsNetBillingFormMixIn,
                                    # ProductBillingMixIn
                                    ):

    def __init__(self, *args, **kwargs):
        ret = super(ProjectGroupCreateBillingForm, self).__init__(
            *args, **kwargs)

        self.sndPaymethod.choices = current_app.config['BILLING_PAY_METHOD_CHOICES']
        self.sndStoreid.data = current_app.config['BILLING_KSNET_STORE_ID']

        product_code = kwargs.get('product_code')
        self.product_code.data = product_code
        self.sndEmail.data = current_user.email
        self.sndReply.data = url_for(
            'portal._project_billing_ksnet_rcv', _external=True)
        self.sndResult.data = url_for('project_group.pg_create_ksnet_result',
                                      product_code=product_code,
                                      _external=True)
        prod = Product.objects.get_or_404(product_code=product_code)
        self.product_obj.data = prod
        self.sndOrdernumber.data = prod.product_code
        self.sndGoodname.data = prod.product_name
        self.unit_price.data = prod.price
        return ret

        return ret

    def validate(self):
        try:
            self.check_by_webhost()

            if int(self.subscription_months.data) != int(self.erks_transaction_quantity.data):
                raise ValidationError('invalid-product-quantity-integrity')

            if self.erks_transaction_product.data != self.product_obj.data:
                raise ValidationError('invalid-product-integrity')
        except ValidationError:
            return False

        return super(ProjectGroupCreateBillingForm, self).validate()

    def save(self):

        project_group = ProjectGroup()
        self.populate_obj(project_group)

        try:
            project_group.save()
        except mongoengine.errors.NotUniqueError:
            # slug  중복시 slug 명칭을 임의로 변경
            project_group.save_as_random_slug()
            flash_warning(lazy_gettext(
                u'프로젝트 ID가 중복되어 %(slug)s로 변경 되었습니다.',
                slug=project_group.slug))

        self.write_project_order(project_group, self.erks_transaction.data)

        return project_group


# class ProjectGroupCreateBillingFormWizardStepTwo(ProjectGroupCreateBillingForm):
#     u"""과금 form 이후 단계에서는 아래 필드들은 보여주지 않는다. 혹은 readonly"""
#     title = HiddenField()
#     slug = HiddenField()
#     description = HiddenField()
#     subscription_months = HiddenField()

#     def __init__(self, *args, **kwargs):
#         ret = super(
#             ProjectGroupCreateBillingFormWizardStepTwo,
#             self).__init__(*args, **kwargs)
#         product_code = self.product_code.data
#         prod = Product.objects(product_code=product_code).first()
#         if prod:
#             self.product_obj.data = prod
#             self.sndOrdernumber.data = prod.product_code
#             self.sndGoodname.data = prod.product_name
#             self.unit_price.data = prod.price
#         return ret


# class ProjectGroupSubscriptionForm(Form,
#                                    # KsNetBillingFormMixIn,
#                                    # ProductBillingMixIn
#                                    ):

#     # subscription은 신규 구독일 경우에는 product_code가 사용자 입력이 필요하고
#     # 연장일때는 product_code가 hidden이어야 한다.
#     # productbillingmixin에서는 hidden_field인데 이 폼에서는 선택해야 하므로 밖으로 꺼내준다.

#     product_code_user_choice = TextField()

#     def __init__(self, *args, **kwargs):
#         ret = super(
#             ProjectGroupSubscriptionForm,
#             self).__init__(*args, **kwargs)
#         # 현재 구독중인 product가 있으면 product_code를 고정한다.
#         if g.project_group.product:
#             prod = g.project_group.product
#             self.product_obj.data = prod
#             self.product_code.data = prod.product_code
#             self.sndOrdernumber.data = prod.product_code
#             self.sndGoodname.data = prod.product_name
#             self.unit_price.data = prod.price

#         self.sndPaymethod.choices = current_app.config['BILLING_PAY_METHOD_CHOICES']
#         self.sndStoreid.data = current_app.config['BILLING_KSNET_STORE_ID']
#         self.sndEmail.data = current_user.email
#         self.sndReply.data = url_for(
#             'portal._project_billing_ksnet_rcv',
#             _external=True)
#         self.sndResult.data = url_for(
#             'project_group._pg_subscription_ksnet_result',
#             slug=g.project_group.slug,
#             _external=True)
#         return ret

#     def validate(self):
#         self.check_by_webhost()

#         if int(self.subscription_months.data) != int(self.erks_transaction_quantity.data):
#             raise ValidationError('invalid-product-quantity-integrity')

#         if self.erks_transaction_product.data != self.product_obj.data:
#             raise ValidationError('invalid-product-integrity')

#         return super(ProjectGroupSubscriptionForm, self).validate()

#     def save(self):
#         project_group = g.project_group
#         self.write_project_order(project_group, self.erks_transaction.data)
#         return project_group


# class ProjectGroupSubscriptionFormWizardStepTwo(ProjectGroupSubscriptionForm):
#     product_obj = ReferenceField(model=Product)
#     subscription_months = HiddenField()
#     product_code = HiddenField()

#     def __init__(self, *args, **kwargs):
#         ret = super(ProjectGroupSubscriptionFormWizardStepTwo, self).__init__(*args, **kwargs)

#         try:
#             months = int(self.subscription_months.data)
#         except ValueError:
#             months = 1
#             self.subscription_months.data = 1

#         if g.project_group.product:
#             product_code = g.project_group.product.product_code
#         else:
#             product_code = request.form['product_code_user_choice']
#         prod = Product.objects(product_code=product_code).first()
#         self.product_obj.data = prod
#         self.sndAmount.data = prod.price * months
#         self.sndOrdernumber.data = prod.product_code
#         self.sndGoodname.data = prod.product_name
#         self.unit_price.data = prod.price

#         # calculate "service-period"
#         service_period_start, service_period_end = \
#             g.project_group.calculate_subscription_period(months)
#         self.sndServicePeriod.data = "{0}-{1}".format(
#             service_period_start.strftime("%Y%m%d"),
#             service_period_end.strftime("%Y%m%d"))

#         return ret


# class ProjectGroupGlossaryForm(Form):
#     use_glossary_master = BooleanField(
#         u'마스터용어사전 사용하기',
#         default=False,
#         description=u'그룹 내 프로젝트가 마스터용어사전을 따르는 용어사전을 생성할 수 있습니다.')

#     # def _build_glossary_queryset():
#     #     from erks.models import Glossary
#     #     return Glossary.objects.filter(
#     #         project_group=g.project_group).order_by('glossary_name')

#     # glossary_master = QuerySetSelectField(
#     #     u'다음 용어집을 사용',
#     #     queryset=_build_glossary_queryset,
#     #     allow_blank=True,
#     #     blank_text=u'--',
#     #     label_attr='glossary_name')


class ProjectGroupForm(
    ProjectGroupBasicMixin,
    model_form(
        ProjectGroup,
        only=(
            'title',
            'description',
            'private',
            'visible',
            'color_theme',
            'theme_key',
            'external_homepage_url',
            'ban_create_project',
            'use_glossary_master',
            'allow_subscribe_all_project_changes',
        ),
        field_args={
            'use_glossary_master': {
                'label': lazy_gettext('마스터용어사전 사용하기'),
                'description': lazy_gettext(
                    '그룹 내 모든 프로젝트가 하나의 대표용어사전을 사용할 수 있습니다.'),
            },
            'external_homepage_url': {
                'label': lazy_gettext(u'외부홈페이지 주소'),
            },
            'external_facebook_url': {
                'label': lazy_gettext(u'페이스북 주소'),
            },
            'external_twitter_url': {
                'label': lazy_gettext(u'트위터 주소'),
            },
            'color_theme': {
                'label': lazy_gettext(u'색상 테마'),
            },
            'theme_key': {
                'label': lazy_gettext(u'테마 키'),
                'description': lazy_gettext(
                    u'프로젝트 그룹의 커스터마이징된 UI를 사용하기 위한 키를 입력합니다.'),
            },
            'ban_create_project': {
                'label': lazy_gettext(u'그룹 내 프로젝트 생성 제한'),
                'description': lazy_gettext(
                    u'관리자를 제외한 일반 사용자의 프로젝트 생성을 제한합니다.'),
            },
            'allow_subscribe_all_project_changes': {
                'label': lazy_gettext('모든 프로젝트 변경사항 구독 가능'),
                'description': lazy_gettext(
                    '모든 프로젝트의 변경사항을 그룹 구성원이라면 누구나 구독 가능합니다.')
            },
        })):
    brand_imgf = FileField(
        lazy_gettext(u'브랜드 이미지'),
        validators=[
            image_file_validator(
                'PROJECT_GROUP_BRAND_IMAGE_MAX_CONTENT_LENGTH'),
        ])
    banner_imgf = FileField(
        lazy_gettext(u'배너 이미지'),
        validators=[
            image_file_validator(
                'PROJECT_GROUP_BANNER_IMAGE_MAX_CONTENT_LENGTH'),
        ])

    def populate_obj(self, obj):
        """image-data는 평소에는 전달되지 않는데 None을 할당해버리면
        데이타가 지워져버리기 때문에 None이면 아예 처리하지 않기."""

        if self.brand_imgf.data is None:
            setattr(self, '_brand_imgf', self.brand_imgf)
            del self.brand_imgf

        if self.banner_imgf.data is None:
            setattr(self, '_banner_imgf', self.banner_imgf)
            del self.banner_imgf

        ret = super(ProjectGroupForm, self).populate_obj(obj)

        if hasattr(self, '_brand_imgf'):
            setattr(self, 'brand_imgf', self._brand_imgf)
            del self._brand_imgf
        if hasattr(self, '_banner_imgf'):
            setattr(self, 'banner_imgf', self._banner_imgf)
            del self._banner_imgf

        return ret


class ProjectGroupMemberInviteForm(Form):
    emails = TextField(
        label=u"초대를 원하는 EMAIL목록",
        validators=[
            validators.Required(u"이메일 주소를 입력해 주세요.")
        ])


class ProjectGroupManagerInviteForm(Form):
    email = ModelSelectField(
        label=lazy_gettext(u'관리자 추가 등록'),
        model=ProjectGroupUser,
        description=lazy_gettext(
            u'관리자로 추가할 사용자의 이메일을 입력해주세요. '
            u'현재 프로젝트 그룹에 속한 사용자만 지정 가능합니다.'),
        validators=[
            validators.Required(),
        ])

    def __init__(self, *args, **kwargs):
        ret = super(ProjectGroupManagerInviteForm, self).__init__(
            *args, **kwargs)
        self.email.queryset = ProjectGroupUser.objects(
            project_group=g.project_group,
            is_moderator=False)
        self.email.label_attr = u'email'
        self.email.allow_blank = True
        self.email.blank_text = lazy_gettext(u'--선택--')
        return ret

    def save(self):
        self.email.data.is_moderator = True
        self.email.data.save()


class ProjectGroupManagerRemoveForm(ProjectGroupManagerInviteForm):

    def save(self):
        self.email.data.is_moderator = False
        self.email.data.save()


class ErccTableWidget(object):
    """
    Renders a list of fields as a set of table rows with th/td pairs.

    If `with_table_tag` is True, then an enclosing <table> is placed around the
    rows.

    Hidden fields will not be displayed with a row, instead the field will be
    pushed into a subsequent table row to ensure XHTML validity. Hidden fields
    at the end of the field list will appear outside the table.
    """
    def __init__(self, with_table_tag=True):
        self.with_table_tag = with_table_tag

    def __call__(self, field, **kwargs):
        html = []
        if self.with_table_tag:
            kwargs.setdefault('id', field.id)
            html.append(
                '''<table %s
    class="table table-condensed table-bordered table-hover">''' % widgets.html_params(**kwargs))
        hidden = ''
        for subfield in field:
            if subfield.type in ('HiddenField', 'CSRFTokenField'):
                hidden += subfield()
            elif subfield.type in ('BooleanField',):
                html.append('<tr><th>%s</th><td>%s</td></tr>' % (
                    subfield.label,
                    subfield(class_='form-control make-switch')))
            else:
                html.append('<tr><th>%s</th><td>%s%s</td></tr>' % (
                    subfield.label,
                    hidden,
                    subfield(class_='form-control')))
                hidden = ''
        if self.with_table_tag:
            html.append('</table>')
        if hidden:
            html.append(hidden)
        return HTMLString(''.join(html))


def _build_table_html(field, ul_class='', **kwargs):
    field_id = kwargs.pop('id', field.id)
    html = [u'<table %s>' % widgets.html_params(id=field_id, class_=ul_class)]
    html.append(u'<tr>')

    # form field가 가지고 있는 모든 fields에 대해서 loop처리
    for k, v in field._fields.items():
        # if k in ['csrf_token']: continue
        if v.type == 'BooleanField':
            html.append(u'<td>%s</td>' % v(class_="form-control make-switch"))
        else:
            html.append(u'<td>%s</td>' % v(class_='form-control'))

    html.append(u'</tr>')
    html.append(u'</table>')
    return HTMLString(u''.join(html))


class ProjectGroupSecurityPrefForm(
    model_form(
        ProjectGroup,
        only=('use_firewall', 'firewall_rules'),
        field_args={
            'use_firewall': {
                'label': lazy_gettext(u'IP기반 접속통제'),
                'description': lazy_gettext(
                    u'<u>관리자를 제외한 모든 사용자가</u> IP기준으로 사용에 제약을 받습니다.')
            },
            'firewall_rules': {
                'label': lazy_gettext(u'통제규칙'),
                'description': lazy_gettext(
                    u'<u>이 설정은 화이트리스트를 관리합니다.</u>'
                    u' 등록한 ip기준으로만 접속이 가능하며, '
                    u' CIDR을 이용한 설정이기때문에 CIDR을 이해하고 적용하시는게 좋습니다.')
            },
        })):

    """
    # 왜 다르게 동작할까? 이렇게 class로 한번 더 감싸면 에러 발생
    # TypeError: 'str' object is not callable
    class EmbeddedFirewallRuleFormField(FormField(model_form(FirewallRule))):
        pass
    firewall_rules = FieldList(EmbeddedFirewallRuleFormField))

    # 이렇게 하면 동작한다.
    firewall_rules = FieldList(FormField(model_form(FirewallRule)))
    """

    firewall_rules = FieldList(
        FormField(
            model_form(
                FirewallRule,
                exclude=[
                    'allow',
                    'seq'
                ],
                field_args={
                    'seq': {'label': u'우선순위'},
                    'allow': {'label': u'사용여부'},
                    'source': {'label': u'IP주소'},
                    'cidr': {'label': u'CIDR'},
                }
            ),
            widget=ErccTableWidget(True),
            default=FirewallRule
        ),
        label=u'통제규칙',
        description=lazy_gettext(
            u'<u>이 설정은 화이트리스트를 관리합니다.</u>'
            u' 등록한 ip기준으로만 접속이 가능하며, 순서(seq)에 맞추어 차례대로 적용합니다.'
            u' CIDR을 이용한 설정이기때문에 CIDR을 이해하고 적용하시는게 좋습니다.')
    )

    def validate_use_firewall(form, field):
        if field.data:
            if request.headers.getlist("X-Forwarded-For"):
                ipaddr = request.headers.getlist("X-Forwarded-For")[0]
            else:
                ipaddr = request.remote_addr

            rules = [FirewallRule.from_json(json.dumps(rule))
                     for rule in form.firewall_rules.data]  # if rule['allow']]
            if len(rules):
                if not any((rule.match(ipaddr) for rule in rules)):
                    raise ValidationError(lazy_gettext(
                        u'자기자신이 block되는 방화벽 설정은 불가능합니다.'))


class ProjectGroupMemberPrefForm(model_form(
    ProjectGroup,
    only=(
        'use_join_with_re',
        'use_join_with_domain',
        'apply_for_newbie_always',
        'join_domain_rules',
        'join_re_rules',
        'join_with_project_invatation',
    ),
    field_args={
        'use_join_with_domain': {
            'label': lazy_gettext(u'도메인기준 사용자 등록'),
            'description': lazy_gettext(
                u'이메일의 도메인 기준으로 신규 가입 사용자를 자동 등록합니다.'),
        },
        'join_domain_rules': {
            'label': lazy_gettext(u'도메인'),
            'description': lazy_gettext(u'@뒤의 도메인을 입력해주세요.')
        },
        'apply_for_newbie_always': {
            'label': lazy_gettext(u'신규가입자 자동검사'),
        },
        'use_join_with_re': {
            'label': lazy_gettext(u'정규표현식으로 사용자 등록하기'),
        },
        'join_with_project_invatation': {
            'label': lazy_gettext(u'프로젝트 초대시 자동 등록'),
            'description': lazy_gettext(
                u'프로젝트 내에서 초대되는 사용자에 대해 자동으로 그룹에도 등록처리됩니다.'),
        }},)):
    _fake = TextField(render_kw={'class': 'form-control'})
    join_domain_rules = FieldList(
        _fake,
        label=u'도메인',
        description=lazy_gettext(u'<u>@을 제외한 도메인 주소</u>를 입력해주세요.'))


# def _build_table_html(field, ul_class='', **kwargs):
#     d = {}
#     d['field_id'] = kwargs.pop('id', field.id)
#     d['ul_class'] = ul_class
#     d['field'] = field
#     return HTMLString(render_template('_formfield_pgpref_notice.html', **d))


class EmbeddedNoticeForm(
    model_form(
        ProjectGroupNotice,
        exclude=[
            'created_by',
            'created_at',
            'publish_begin_at',
            'publish_end_at'
        ],
        field_args={
            'seq': {
                'label': lazy_gettext(u'순서')
            },
            'content': {
                'label': lazy_gettext(u'내용')
            },
        })):
    pass


class ProjectGroupNoticePrefForm(
    model_form(
        ProjectGroup,
        only=(
            'show_notices',
            'notices',
        ),
        field_args={
            'notices': {
                'label': lazy_gettext(u'공지사항목록'),
            }
        })):
    notices = FieldList(
        FormField(EmbeddedNoticeForm, widget=_build_table_html),
        label=lazy_gettext(u'공지사항목록'),
        min_entries=1)
    # created_at = DateTimeField(
    #     label=lazy_gettext(u'시작시간', format='%Y-%m-%dT%H:%M:%S'),
    #     validators=(
    #         validators.Optional(),
    #     ))


class ProjectGroupProjectPrefForm(
    model_form(
        ProjectGroup,
        only=(
            'ban_create_project',
        ),
        field_args={
            'ban_create_project': {
                'label': lazy_gettext(u'프로젝트 생성 제한'),
                'description': lazy_gettext(
                    u'관리자를 제외한 일반 사용자의 프로젝트 생성을 제한합니다.'),
            }
        })):
    pass


class ProjectGroupUserRoleForm(model_form(
        ProjectGroupUser,
        only=(
            'is_moderator',
            'is_termer',
        )
)):
    is_moderator = BooleanField(lazy_gettext(u'관리자 지정'))
    is_termer = BooleanField(lazy_gettext(u'용어관리자 지정'))


class ProjectGroupInviteMemberForm(Form):
    '''project_group 사용자초대 form
    project와 유사하지만,
    project_group은 외부사용자초대에 대한 logic이 없습니다.'''
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

        project_group = g.project_group

        receivers = [{
            'user_email': email,
            'user': User.objects(email=email, verified=True).first(),
            'is_user': False,
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

            if r['is_user'] and not r['is_project_group_member']:
                r['ok'] = True
                msg, status = gettext(u'초대 가능한 사용자입니다.'), 'success'  # ok
            else:
                if r['is_project_group_member']:
                    msg, status = gettext(u'이미 프로젝트그룹 사용자입니다.'), 'info'
                else:
                    msg, status = gettext(u'알 수 없는 사용자입니다.'), 'danger'

            r['status_message'] = msg
            r['status'] = status
            # if r['user']:
            #     r['user'] = json.loads(r['user'].to_json())

        return receivers
