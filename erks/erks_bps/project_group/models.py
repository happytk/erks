# -*-encoding: utf-8-*-

import six
import random
import logging as logger
import ipaddress

from datetime import datetime
from builtins import str as text  # python3 compatible

import mongoengine

from flask import url_for, current_app
from flask_login import current_user
from flask_babel import gettext
from erks.extensions import db
from erks.signals import (
    on_created_project_group,
    on_changed_project_group,
    on_joined_to_project_group,
)
from erks.errors import (
    ProjectGroupIntegrityError,
)
# from erks.erks_bps.billing.models import BillingMixin
from erks.utils import (
    JsonifyPatchMixin,
)

COLOR_THEME_CHOICES = (
    ('', 'default'),
    ('default', 'black'),
    ('blue', 'blue'),
    ('grey', 'grey'),
    ('light', 'light'),
    ('darkblue', 'darkblue'),
)

THEME_KEYS = ['skb']


class ProjectGroupAppereance(object):

    brand_imgf = db.ImageField(
        collection_name='project_group_brand_images',
        size=(600, 600, True),
        thumbnail_size=(140, 140, True))
    banner_imgf = db.ImageField(
        collection_name='project_group_banner_images',
        size=(1900, 600, True),
        thumbnail_size=(600, 190, True))

    color_theme = db.StringField(choices=COLOR_THEME_CHOICES)
    theme_key = db.StringField(max_length=255)

    def has_theme(self):
        return self.theme_key and self.theme_key in THEME_KEYS

    @property
    def nav_html(self):
        if self.theme_key and self.theme_key in THEME_KEYS:
            return 'theme/{theme_key}/project/base_{theme_key}.html'.format(theme_key=self.theme_key)
        else:
            return "_nav.html"

    @property
    def base_html(self):
        if self.theme_key and self.theme_key in THEME_KEYS:
            return 'theme/{theme_key}/base_{theme_key}.html'.format(theme_key=self.theme_key)
        else:
            return "base.html"

    @property
    def project_base_html(self):
        if self.theme_key and self.theme_key in THEME_KEYS:
            return 'theme/{theme_key}/project/base_{theme_key}.html'.format(theme_key=self.theme_key)
        else:
            return "project/base.html"

    @property
    def base4erc_html(self):
        if self.theme_key and self.theme_key in THEME_KEYS:
            return 'theme/{theme_key}/base4erc_{theme_key}.html'.format(theme_key=self.theme_key)
        else:
            return "base4erc.html"

    @property
    def brand_img_url(self):
        if self.brand_imgf:
            return url_for('project_group.brand_img', slug=self.slug)
        else:
            return url_for(
                'static',
                filename='img/r3/Project_thumb_768x573_04.jpg')

    @property
    def banner_img_url(self):
        if self.banner_imgf:
            return url_for('project_group.banner_img', slug=self.slug)
        else:
            return url_for('static', filename='img/rev2/img2.jpg')


class ProjectGroupNotice(db.EmbeddedDocument):
    # project_group = db.ReferenceField('ProjectGroup')
    seq = db.IntField(default=0)
    created_at = db.DateTimeField(default=datetime.now, required=True)
    created_by = db.ReferenceField('User', required=True)
    publish_begin_at = db.DateTimeField(
        default=datetime.now, required=True)
    publish_end_at = db.DateTimeField(
        default=datetime.now, required=True)
    content = db.StringField(required=True)

# class TableFormField(db.EmbeddedDocumentField):
#     """
#     아예 전용 field를 만들어서 사용할 수도 있다.
#     """
#     def __init__(self, obj, **kwargs):
#         super(ProjectGroupNoticeField,self).__init__(obj, **kwargs)
#         self._obj = obj
#     def to_form_field(self, model, kwargs):
#         def _build_table_html(field, ul_class='', **kwargs):
#             d = {}
#             d['field_id'] = kwargs.pop('id', field.id)
#             d['ul_class'] = ul_class
#             d['field'] = field
# return HTMLString(render_template('_formfield_as_table.html', **d))
#         kwargs = {
#             'validators': [],
#             'filters': [],
#             'default': self.default or self.document_type_obj,
#             'widget': _build_table_html, #widgets.ListWidget(),
#         }
#         inline_form = model_form(self._obj)
#         return fields.FormField(inline_form, **kwargs)


class FirewallRule(db.EmbeddedDocument):

    seq = db.IntField(default=0)
    allow = db.BooleanField(default=True)
    source = db.StringField(max_length=50, required=True)
    cidr = db.IntField(max_value=32, required=True)

    def to_ipcidr(self):
        return u"{0}/{1}".format(self.source, self.cidr)

    def match(self, ipaddr):
        # if isinstance(ipaddr, str) or isinstance(ipaddr, unicode):
        if isinstance(ipaddr, six.text_type):
            ipaddr = ipaddress.ip_address(text(ipaddr))
        return ipaddr in ipaddress.ip_network(self.to_ipcidr())


class ProjectGroupGlossaryMasterMixin(object):
    use_glossary_master = db.BooleanField(default=False)

    @property
    def glossary_master(self):
        from erks.models import GlossaryMaster
        return GlossaryMaster.objects(project_group=self).first()
    # glossary_master = db.ReferenceField('GlossaryMaster')

    @property
    def queryset_master_term(self):
        from erks.models import Term
        if self.use_glossary_master and self.glossary_master:
            return Term.objects(glossary=self.glossary_master)
        else:
            return Term.objects(id='0' * 24)  # empty

    @property
    def queryset_master_term_request(self):
        from erks.models import TermMasterRequest
        if self.use_glossary_master and self.glossary_master:
            return TermMasterRequest.objects(
                glossary_master=self.glossary_master)
        else:
            return TermMasterRequest.objects(id='0' * 24)  # dummy

    @property
    def queryset_glossary(self):
        from erks.models import Glossary
        return Glossary.head_objects(project_group=self)

    def create_glossary_master(self):
        from erks.models import GlossaryMaster
        if self.glossary_master:
            raise ProjectGroupIntegrityError(gettext(
                '프로젝트그룹 마스터용어집은 이미 존재합니다'))

        # glossary = GlossaryMaster.objects(project_group=self).first()
        # if glossary is None:
        glossary = GlossaryMaster()
        glossary.project_group = self
        glossary.glossary_name = self.slug  # temporary
        glossary.save()

        logger.debug('glossary_master is created.')
        # self.glossary_master = glossary
        # self.save()


class ProjectGroupLimitFactors(object):

    # project_group billing-type에 따라 count에 제한을 둠.
    da_cnt_limit = db.IntField(default=100)
    project_cnt_limit = db.IntField(default=100)
    member_cnt_limit = db.IntField(default=100)

    # project 생성통제
    ban_create_project = db.BooleanField(default=False)

    # ip기반의 위치통제를 하기 위함
    use_firewall = db.BooleanField(default=False)
    firewall_rules = db.ListField(db.EmbeddedDocumentField(FirewallRule))

    def check_allowed_ip(self, ipaddr_str):
        ipaddr = ipaddress.ip_address(text(ipaddr_str))
        rules = [rule for rule in self.firewall_rules if rule.allow]

        if len(rules) == 0:
            return True

        return any((rule.match(ipaddr) for rule in rules))

    def is_firewall_working(self):
        return self.use_firewall and len(self.firewall_rules) > 0


class ProjectGroupNotices(object):

    show_notices = db.BooleanField(default=True)
    notices = db.ListField(db.EmbeddedDocumentField(ProjectGroupNotice))
    # notices = db.ListField(ProjectGroupNoticeField())

    @property
    def queryset_notice(self):
        from erks.models import ProjectGroupNotice
        return ProjectGroupNotice.objects(project_group=self, use_yn=True)

    @property
    def queryset_qna(self):
        from erks.models import ProjectGroupQnA
        return ProjectGroupQnA.objects(project_group=self, use_yn=True)


class ProjectGroupMy(object):

    @classmethod
    def my(cls, user=None):
        if user is None:
            if current_user and current_user.is_active:
                user = current_user._get_current_object()
            else:
                return []

        return (
            pg.project_group
            for pg in ProjectGroupUser.objects(user=user).order_by('title')
        )

    @property
    def my_grade(self):
        return self.get_grade(current_user._get_current_object())

    def get_grade(self, user):
        if user and user.is_active:
            entry = ProjectGroupUser.objects(
                project_group=self,
                user=user
            ).first()
            if entry is None:
                return 'guest'
            else:
                if entry.is_owner:
                    return 'owner'
                elif entry.is_moderator:
                    return 'manager'
                elif entry.is_termer:
                    return 'termer'
                else:
                    return 'member'
        else:
            return 'guest_not_loggined'

    @property
    def managers(self):
        return (entry.user for entry in self.queryset_manager)

    @property
    def members(self):
        return (entry.user for entry in self.queryset_member)

    @property
    def queryset_manager(self):
        return ProjectGroupUser.objects(project_group=self)\
            .filter(
                mongoengine.Q(is_moderator=True) |
                mongoengine.Q(is_owner=True)
        )

    @property
    def queryset_member(self):
        return ProjectGroupUser.objects(project_group=self)


class ProjectGroupMemberJoin(object):

    # members = db.ListField(db.ReferenceField('User'))

    use_join_with_re = db.BooleanField(default=False)
    use_join_with_domain = db.BooleanField(default=False)

    # 신규사용자에 대해 자동등록검사
    apply_for_newbie_always = db.BooleanField(default=False)

    join_domain_rules = db.ListField(db.StringField(max_length=1000))
    join_re_rules = db.ListField(db.StringField(max_length=1000))

    # 프로젝트 초대시 자동으로 그룹사용자 등록
    join_with_project_invatation = db.BooleanField(default=False)

    # 프로젝트그룹내 사용자를 검색해서 프로젝트에 초대할 수 있는지 여부
    can_search_member = db.BooleanField(default=True)

    # 프로젝트그룹내 사용자를 검색해서 프로젝트에 초대할 수 있는지 여부
    can_invite_oubound_user = db.BooleanField(default=False)

    def join(self, user):
        return ProjectGroupUser(project_group=self, user=user).save()

    def leave(self, user):
        ProjectGroupUser.objects(project_group=self, user=user).delete()

    def test_joinrule(self, email):
        chunks = email.split('@')
        if len(chunks) < 2:
            return False

        if self.use_join_with_domain and \
                any([
                    domain == chunks[1]
                    for domain in self.join_domain_rules
                ]):
            return True

        return False

    def clean(self):
        self.join_domain_rules = list(set(self.join_domain_rules))
        self.join_domain_rules = list(filter(
            lambda x: len(x),
            self.join_domain_rules)
        )

        self.join_re_rules = list(set(self.join_re_rules))
        self.join_re_rules = list(filter(
            lambda x: len(x),
            self.join_re_rules)
        )


class ProjectGroup(db.Document,
                   ProjectGroupNotices,
                   ProjectGroupAppereance,
                   ProjectGroupLimitFactors,
                   ProjectGroupMy,
                   ProjectGroupMemberJoin,
                   ProjectGroupGlossaryMasterMixin,
                   # BillingMixin
                   ):
    """프로젝트를 그룹하여 관리하는 객체.
    project는 한개의 group에 종속된다.
    default라는 이름으로 기본 project_group이 항상 존재해야 함.
    """

    meta = {
        'indexes': [
            {
                'fields': [
                    'slug'
                ],
                'unique': True
            },
        ],
    }

    ####################################################################
    # fields
    ####################################################################
    title = db.StringField(required=True, max_length=255, min_length=2)
    slug = db.StringField(required=True, max_length=255, min_length=2)
    description = db.StringField(required=True, max_length=4000)
    external_homepage_url = db.URLField(max_length=1000)

    private = db.BooleanField(default=False)
    visible = db.BooleanField(default=True)

    created_at = db.DateTimeField(default=datetime.now, required=True)
    created_by = db.ReferenceField('User')

    allow_subscribe_all_project_changes = db.BooleanField(default=False)

    ####################################################################
    # properties
    ####################################################################
    @property
    def queryset_project(self):
        from erks.erks_bps.project.models import Project
        return Project.objects(project_group=self)

    @property
    def queryset_project_group_user(self):
        return ProjectGroupUser.objects(project_group=self)

    @property
    def url(self):
        return url_for('project_group.list_projects', slug=self.slug)

    @property
    def is_not_default(self):
        return self.slug != 'default'

    @property
    def is_default(self):
        return self.slug == 'default'

    @classmethod
    def default(cls):
        slug = current_app.config['DEFAULT_PROJECT_GROUP_SLUG']
        default_project_group = ProjectGroup.objects(slug=slug).first()

        # if not default_project_group.theme_key and current_app.config['DEFAULT_PROJECT_GROUP_THEME_KEY']:
        #     default_project_group.theme_key = current_app.config['DEFAULT_PROJECT_GROUP_THEME_KEY']

        return default_project_group

    ####################################################################
    # methods
    ####################################################################
    def __unicode__(self):
        return self.slug

    def clean(self):
        # project_group에 속한 여러개의 mixins의
        # clean method를 차례로 호출
        for base in ProjectGroup.__bases__:
            try:
                base.clean(self)
            except AttributeError:
                pass

    def save_as_random_slug(self):
        logger.debug("save_as_random_slug called")
        try:
            # import pdb; pdb.set_trace()
            self.slug = self.slug + str(random.randrange(1, 1000))
            self.save()
            logger.debug(
                "slug {0}, "
                "save_as_random_slug saved".format(self.slug)
            )
        except mongoengine.errors.NotUniqueError:
            self.save_as_random_slug()

    def save(self, *args, **kwargs):
        is_new = not self.id
        self.is_free = False  # project_group always shouldn't be free.
        ret = super(ProjectGroup, self).save(*args, **kwargs)
        # if kwargs.get('emit_signals', True) and self.is_not_default:
        if is_new:
            on_created_project_group.send(self)
        else:
            on_changed_project_group.send(self)
        return ret


class ProjectGroupUser(JsonifyPatchMixin,
                       db.Document):

    meta = {
        'indexes': [
            {
                'fields': [
                    'project_group',
                    'user'
                ],
                'unique': True
            },
        ],
    }

    ####################################################################
    # fields
    ####################################################################
    project_group = db.ReferenceField(
        'ProjectGroup',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)
    user = db.ReferenceField(
        'User',
        required=True,
        reverse_delete_rule=mongoengine.CASCADE)

    is_owner = db.BooleanField(default=False)
    is_moderator = db.BooleanField(default=False)
    is_termer = db.BooleanField(default=False)

    last_visited_at = db.DateTimeField(default=datetime.now)
    created_at = db.DateTimeField(default=datetime.now)

    # ui
    project_layout = db.StringField(default='boxed')

    render_template_path = "project_group/_members_tbl_row.html"

    ####################################################################
    # cached properties
    ####################################################################
    user_email = db.EmailField(max_length=255)

    ####################################################################
    # methods
    ####################################################################
    def __unicode__(self):
        return '{0}:{1}'.format(self.project_group.slug, self.user.email)

    def clean(self):
        self.user_email = self.user.email

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        logger.debug('post save : %s' % document)
        on_joined_to_project_group.send((document.user, document.project_group))


mongoengine.signals.post_save.connect(ProjectGroupUser.post_save, sender=ProjectGroupUser)
