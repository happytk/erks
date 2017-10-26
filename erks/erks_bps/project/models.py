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


class ProjectGlossaryDerivedMixin(object):
    @property
    def queryset_glossary_derived(self):
        from erks.models import GlossaryDerived
        return GlossaryDerived.head_objects(project=self)

    def create_glossary_derived(self):
        from erks.models import GlossaryDerived
        logger.debug(f'New glossary-derived for {self} is created.')
        return GlossaryDerived(project=self).save()


class ProjectSchemaCollectorMixin(object):
    @property
    def context_model_schema_collector(self):
        '''schemacollector per model'''
        from erks.models import SchemaCollector
        return [
            (
                model,
                SchemaCollector.objects(id=model.schema_collector).first() if (hasattr(model, 'schema_collector') and model.schema_collector) else None,
                model.queryset_schema_diff.order_by('-created_at').first(),
            )
            for model in self.queryset_model.order_by('name')
        ]

    @property
    def physical_model_matched_rate(self):
        reports = self.queryset_model_schmea_diff.all()

        def _(obj, name):
            if hasattr(obj, name):
                try:
                    return int(getattr(obj, name))
                except ValueError:
                    pass
            return 0

        total_cnt = sum([_(r, 'matched') + _(r, 'not_matched') for r in reports])
        matched_cnt = sum([_(r, 'matched') for r in reports])
        return round(matched_cnt / total_cnt, 2) if total_cnt else 0


class ProjectReportMixin(object):
    @property
    def context_model_report(self):
        from erks.models import GlossaryBase
        return [
            (
                model,
                GlossaryBase.head_objects(id=model.glossaryId).first() if (hasattr(model, 'glossaryId') and model.glossaryId) else None,
                model.queryset_model_report.order_by('-created_at').first(),
            )
            for model in self.queryset_model.order_by('name')
        ]

    @property
    def context_model_report_finished(self):
        from erks.models import GlossaryBase
        return [
            (
                model,
                GlossaryBase.head_objects(id=model.glossaryId).first() if (hasattr(model, 'glossaryId') and model.glossaryId) else None,
                model.queryset_model_report(status='finished').order_by('-created_at').first(),
            )
            for model in self.queryset_model.order_by('name')
        ]

    @property
    def queryset_model_report(self):
        from erks.models import ProjectModelReport
        return ProjectModelReport.objects(project=self)

    @property
    def queryset_model(self):
        from erks.erks_bps.erc.models import Model
        return Model.head_objects(prjId=str(self.id))

    @property
    def queryset_model_schmea_diff(self):
        from erks.models import ModelSchemaDiff
        return ModelSchemaDiff.objects(project=self.id)


class ProjectInvatationMixin(object):

    # 사용자도 멤버초대를 할 수 있는지
    allow_invitation_by_member = db.BooleanField(default=True)

    # TODO: 이 필드는 더 이상 사용하지 않습니다. 정리해주세요.
    # waiting_members = db.ListField(db.ReferenceField('User'))
    # invited_members = db.ListField(db.ReferenceField('User'))
    # auto_approve_requested_user = db.BooleanField(default=False)
    # auto_approve_invite_user = db.BooleanField(default=False)
    # 사용하지 않는 필드모음 끝.

    @property
    def waiting_invited_members(self):
        """프로젝트에 초대된 멤버목록을 보여줍니다."""
        from erks.models import ProjectWaitingUserOutbound
        cls = ProjectWaitingUserOutbound
        return (
            entry.user
            for entry in cls.objects(project=self).only('user'))

    @property
    def waiting_requested_members(self):
        """프로젝트에 가입요청한 멤버목록을 보여줍니다."""
        from erks.models import ProjectWaitingUserInbound
        cls = ProjectWaitingUserInbound
        return (
            entry.user
            for entry in cls.objects(project=self).only('user'))

    @property
    def members_cnt(self):
        '''project의 의미있는 member는 가입된 사용자 수 + 초대된 사용자 수.
        프로젝트 구성원이 의지적으로 포함시키지 않은 request member는 제외한다.'''
        from erks.models import ProjectUserBase
        return ProjectUserBase.objects(project=self).count() - \
            len(list(self.waiting_requested_members))

    def _available_member_cnt(self):
        from erks.models import ProjectUser, ProjectWaitingUserOutbound
        members_cnt = ProjectUser.objects(project=self).count()
        waiting_invited_members_cnt = ProjectWaitingUserOutbound.objects(
            project=self).count()
        return (
            self.product.member_cnt_limit -
            members_cnt -
            waiting_invited_members_cnt
        )

    def is_new_member_available(self, new_member_cnt=1):
        """새로운 멤버를 받을 수 있는지 체크."""
        if current_app.config['BILLING']:
            product = self.product
            if product is None:
                return False
            elif product.member_cnt_limit == 0:
                return True
            else:
                return self._available_member_cnt() - new_member_cnt >= 0
        else:
            return True

    def invite(self, email, inviter):
        '''email로 초대하기 (외부 사용자를 포함해야 하므로 사용자객체 아님)
        여러가지 방향이 있었지만 현재는 invite의 경우 별도의 승인없이 무조건 편입한다.
        invite는 의지적인 행동이기 때문에 별다른 검증을 거치지 않는 것으로 process 수립

        todo: code is messy. please tide up.
        '''

        from erks.models import ProjectUser, ProjectWaitingUserOutbound
        logger.debug('inviting %s', email)
        pg = self.project_group

        if (self.get_grade(inviter) == self.ORGANIZER or
                self.allow_invitation_by_member) and \
                self.is_new_member_available():

            try:
                user = User.objects.get(email=email)
                pgu = pg.queryset_member.filter(user=user).first()
                if pgu:
                    try:
                        ProjectUser(
                            project=self,
                            user=user,
                            project_group_user=pgu).save()
                        ret = True
                        logger.debug(
                            'inviting process for inbound-user(%s)' % email)
                    except NotUniqueError:
                        logger.warning(
                            'already registered project-member(%s)', email)
                        ret = False
                else:
                    logger.warning(
                        'user(%s)-does-not-in-project-group(%s).', email, pg)
                    ret = False
            except User.DoesNotExist:
                if pg.can_invite_oubound_user:
                    try:
                        invitee = ProjectWaitingUserOutbound(
                            project=self,
                            user=email).save()
                        invitee.sendmail()
                        ret = True
                        logger.debug(
                            'inviting process for outbound-user(%s)' % email)
                    except NotUniqueError:
                        logger.warning('already registered outbound-user')
                        ret = False
                else:
                    logger.warning(
                        'outbound user(%s) cannot'
                        ' join project-group(%s).'
                        ' check the pref.', email, pg)
                    ret = False
        else:
            ret = False

        return ret

    def leave(self, user):
        '''Project탈퇴는 MEMBER는 가능, OWNER는 불가능하다.
        탈퇴 성공여부를 True/False로 리턴'''
        from erks.models import ProjectUser
        entry = ProjectUser.objects(
            project=self, user=user, is_owner=False).first()
        if entry:
            entry.delete()
            return True
        else:
            return False

    def request_to_join(self, user, message=u''):
        '''외부 사용자의 의지적인 합류 요청.
        '''
        from erks.models import ProjectWaitingUserInbound
        try:
            ProjectWaitingUserInbound(
                project=self, user=user, asked_message=message).save()
            logger.debug('inviting process for inbound-user(%s)' % user)
            ret = True
        except NotUniqueError:
            logger.warning('already registered project-waiting-member')
            ret = False
        return ret


class ProjectRecommendationMixin(object):
    """프로젝트 추천하기."""

    picked = db.BooleanField(default=False)
    display_priority = db.IntField(default=0)

    @classmethod
    def _random(cls, limit, project_group, picked=False):
        u"""추천알고리즘없이 임의로 프로젝트 골라오기."""
        kw = dict(
            private=False,
            visible=True,
            demo=False,
            project_group=project_group)
        if picked:
            kw['picked'] = True  # picked는 false일때는 true/false모두 챙긴다.

        projects = Project.objects(**kw).no_dereference().only('id')
        if len(projects):
            random.shuffle(list(projects))
            projects = [
                projects[i].reload()
                for i in range(min(limit, len(projects)))
            ]
            projects.sort(key=lambda x: -x.display_priority)
            return projects
        else:
            return []

    @classmethod
    def random(cls, limit=4, project_group=None):
        """추천알고리즘없이 임의로 프로젝트 골라오기.

        PROJECT:
        이 함수들은 성능이 좋지 않아서 PRODUCTION에서는 사용할 수 없습니다.
        batch로 project list를 준비하던가 해야겠음

        """
        if project_group is None:
            project_group = ProjectGroup.default()

        # picked priority
        selected = cls._random(limit=limit,
                               picked=True,
                               project_group=project_group)

        if len(selected) < limit:
            # 만약 limit만큼 채워지지 않았으면 조금 더 얻어오기
            chunks = cls._random(
                limit=limit - len(selected),
                project_group=project_group)
            selected.extend(chunks)

        # shuffle!
        # random.shuffle(selected)
        return selected


# class ProjectBillingMixin(BillingMixin):

#     def available_to_create_free_project(self):
#         """무료프로젝트를 가지고 있지 않다면 생성 가능하다."""
#         return len(Project.my_free_project()) == 0

#     def available_to_convert_free_project(self):
#         """유료구독이 끝났을 때, 무료프로젝트를 가지고 있지 않다면, 무료 프로젝트로 전환가능하다."""
#         return self.is_expired and self.available_to_create_free_project()

#     def convert_free_project(self):
#         """무료프로젝트로 전환한다."""
#         if self.product is None or not self.product.support_private:
#             self.private = False
#             self.visible = True

#         self.is_free = True
#         # self.product = Product.default()
#         self.save()

#     def convert_paid_project(self):
#         """유료프로젝트로 전환한다."""
#         # self.private = True
#         self.is_free = False
#         self.save()


class ProjectUserMixin(object):
    @classmethod
    def my(cls, project_group=None):
        """current_user의 소유 프로젝트 목록."""
        from erks.models import ProjectUser
        if project_group is None:
            project_group = ProjectGroup.default()
        user = current_user._get_current_object()

        pgu = ProjectGroupUser.objects(
            project_group=project_group,
            user=user).first()
        return (
            entry.project
            for entry in ProjectUser.objects(
                project_group_user=pgu,
                user=user,
                is_owner=True).only('project').all()
        )

    @classmethod
    def my_belonged(cls, project_group=None):
        """current_user의 소속된 프로젝트 목록. 소유를 포함한다."""
        from erks.models import ProjectUser
        if project_group is None:
            project_group = ProjectGroup.default()
        user = current_user._get_current_object()
        project_group_user = ProjectGroupUser.objects(
            project_group=project_group,
            user=user).first()
        return ProjectUser.objects(
            project_group_user=project_group_user,
            user=user).exclude('user', 'project_group_user')

    @classmethod
    def my_visit_log(cls, limit=4, skip=0, project_group=None):
        """방문한 프로젝트 목록"""
        from erks.models import ProjectUser
        if project_group is None:
            project_group = ProjectGroup.default()
        user = current_user._get_current_object()
        project_group_user = ProjectGroupUser.objects(
            project_group=project_group, user=user).first()
        return (
            entry.project
            for entry in ProjectUser.objects(
                project_group_user=project_group_user,
                user=user)
            .only('project')
            .order_by('-last_visited_at')
            .skip(skip)
            .limit(limit)
        )

    @classmethod
    def my_free_project(cls):
        return [
            project
            for project in cls.my(
                project_group=ProjectGroup.default())
            if project.is_free
        ]

    @property
    def queryset_member(self):
        from erks.models import ProjectUser
        return ProjectUser.objects(project=self)


class Project(JsonifyPatchMixin,
              AuditableMixin,
              db.Document,
              # ProjectBillingMixin,
              # ProjectGlossaryDerivedMixin,
              ProjectInvatationMixin,
              # ProjectRecommendationMixin,
              # ProjectReportMixin,
              # ProjectSchemaCollectorMixin,
              ProjectUserMixin,
              ):

    title = db.StringField(required=True, max_length=40, min_length=2)
    # created_at = db.DateTimeField(default=datetime.now, required=True)

    private = db.BooleanField(default=False)
    visible = db.BooleanField(default=True)
    demo = db.BooleanField(default=False)

    description = db.StringField()
    contact = db.StringField()
    profile_imgf = db.ImageField(collection_name='project_images',
                                 size=(600, 600, True),
                                 thumbnail_size=(140, 140, True),)
    project_group = db.ReferenceField('ProjectGroup', required=True)
    project_group_managed = db.BooleanField(default=False)

    # modified_at = db.DateTimeField(
    #     default=datetime.now, required=True)

    meta = {
        'ordering': ['-modified_at', '-created_at']
    }

    ####################################################################
    # PROJECT내에서 사용되는 GRADE
    ####################################################################
    ORGANIZER = u'owner'
    MEMBER = u'member'
    MODELER = u'modeler'
    TERM_MANAGER = u'termer'
    WAITING_MEMBER = u'waiting_member'
    GUEST = u'guest'

    @property
    def base_html(self):
        if self.project_group:
            return self.project_group.project_base_html
        else:
            return "project/base.html"

    @property
    def base4erc_html(self):
        if current_user.is_authenticated:
            if self.project_group:
                return self.project_group.base4erc_html
            else:
                return "base4erc.html"
        else:
            return ProjectGroup.default().base4erc_html

    ####################################################################
    # properties
    ####################################################################
    @property
    def queryset_project_user(self):
        from erks.models import ProjectUserBase
        return ProjectUserBase.objects(project=self)

    @property
    def queryset_post(self):
        from erks.models import Post
        return Post.objects(project=self)
    # @property
    # def queryset_glossary(self):
    #     from erks.models import GlossaryBase
    #     return GlossaryBase.head_objects(project=self)

    @property
    def queryset_user(self):
        '''todo: mongodb와 document 설계 한계로 인해서 사용자객체의 queryset
        형태로 구현하기에는 현재로서는 어려워보임.'''

        # code = """
        # function(field) {
        #     var docs = [];
        #     db['project_user_base'].find(
        #        {project: ObjectId(options.project_id)}
        #    ).forEach(function(doc) {
        #         //docs.push(db[collection].findOne({_id: doc.user}));
        #         docs.push(doc.user);
        #     });
        #     return docs;
        # }
        # """
        # return User.objects.exec_js(code, 'id', project_id=str(self.id))

        raise NotImplementedError()

    # @property
    # def context_term_managers(self):
    #     '''현재 project, glossary에 속해있는 용어관리자를 return'''
    #     return [
    #         entry.user
    #         for entry in self.queryset_project_user.filter(
    #             is_termer=True).only('user', 'can_manage_all_glossaries',
    #                                  'manageable_glossaries')
    #         if entry.can_manage_all_glossaries or (
    #             entry.manageable_glossaries and
    #             g.glossary in entry.manageable_glossaries)
    #     ]

    @property
    def owner(self):
        project_owner = self.queryset_project_user.filter(
            is_owner=True).only('user').first()
        return project_owner.user

    @property
    def members(self):
        # TODO: 속도개선을 위해 iterable하고 container type의 객체를 return하도록
        return [
            entry.user
            for entry in self.queryset_project_user.only('user')
        ]

    @property
    def term_managers(self):
        # TODO: 속도개선을 위해 iterable하고 container type의 객체를 return하도록
        return [
            entry.user
            for entry in self.queryset_project_user.filter(
                is_termer=True).only('user')
        ]

    @property
    def modelers(self):
        # TODO: 속도개선을 위해 iterable하고 container type의 객체를 return하도록
        return [
            entry.user
            for entry in self.queryset_project_user.filter(
                is_modeler=True).only('user')
        ]

    @property
    def url(self):
        return url_for('project.index', project_id=self.id)

    @property
    def external_url(self):
        return url_for('project.index', project_id=self.id, _external=True)

    ####################################################################
    # queryset
    ####################################################################
    @db.queryset_manager
    def demo_objects(doc_cls, queryset):
        return queryset.filter(demo=True)

    @db.queryset_manager
    def visible_objects(doc_cls, queryset):
        '''프로젝트포털에 노출가능한 것만 보여준다.'''
        # TODO: 내 것은 무조건 보여야 한다.
        return queryset.filter(
            (Q(visible=True) | Q(visible=None)) & Q(demo=False))

    ####################################################################
    # methods
    ####################################################################
    def save(self, *args, **kwargs):
        # NOTIFY_MAP = {
        #     'title': dict(message=lazy_gettext(u'프로젝트명이 \'%s\'로 변경되었습니다.' % self.title, typ='project'),
        #     'private': dict(message=lazy_gettext(u'이 프로젝트는 %s입니다.' % (lazy_gettext(u'공개', lazy_gettext(u'비공개')[self.private], typ='project'),
        #     'visible': dict(message=lazy_gettext(u'이 프로젝트는 %s.' % (lazy_gettext(u'검색되지 않습니다.', lazy_gettext(u'검색에 노출됩니다.')[self.visible], typ='project'),
        #     'description': dict(message=lazy_gettext(u'상세 설명 부분이 변경되었습니다.', typ='project'),
        #     'profile_imgf': dict(message=lazy_gettext(u'프로젝트 이미지가 변경되었습니다.', typ='project'),
        # }

        if self.id:
            # [self.notify(**NOTIFY_MAP[fieldname])
            #     for fieldname in self._changed_fields
            #     if fieldname in NOTIFY_MAP]
            # OWNER변경에 대한 NOTIFICATION처리, OWNER가 종종 알수없이 _changed_fields에
            # 들어가있다.
            # if 'owner' in self._changed_fields:
            #     self.notify(message=lazy_gettext(u'{{user.email}} 사용자는 관리자입니다.',
            #                 user=self.owner, typ='user')
            #     on_changed_project_owner.send(self)
            on_changed_project.send(self)
            ret = super(Project, self).save(*args, **kwargs)
        else:
            # You can only reference documents once they have been saved to the
            # database
            ret = super(Project, self).save(*args, **kwargs)
            on_created_project.send(self)
            # on_changed_project_owner.send(self)
            # self.notify(
            #     message=lazy_gettext(u'프로젝트가 생성되었습니다 by {{user.email}}', user=self.owner, typ='project')
            # self.notify(message=lazy_gettext(u'{{user.email}} 사용자는 관리자입니다.',
            #             user=self.owner, typ='user')
        return ret

    def __unicode__(self):
        return self.title

    def __lt__(self, other):
        return str(self) < str(other)

    def __gt__(self, other):
        return str(self) > str(other)

    def clean(self):

        # free-project-cannot-be-private
        # self.id가 없을때 product를 참고하면 오류발
        if current_app.config['BILLING']:
            if self.id and \
               (self.product is None or not self.product.support_private):
                self.private = False
                self.visible = True

        # project-group-check
        if self.project_group is None:
            self.project_group = ProjectGroup.default()

    def get_grade(self, user):
        from erks.models import (
            ProjectUser,
            ProjectUserBase,
            ProjectWaitingUserInbound,
        )
        # 미로그인사용자도 사용할 수 있는 함수
        # if user.is_active:
        #     if user == self.owner:
        #         return self.ORGANIZER
        #     elif user in self.modelers:
        #         return self.MODELER
        #     elif user in self.term_managers:
        #         return self.TERM_MANAGER
        #     elif user in self.members:
        #         return self.MEMBER
        #     elif user in self.waiting_members:
        #         return self.WAITING_MEMBER
        #     # elif user in self.invited_members:
        #     #     return self.WAITING_MEMBER
        # else:
        #     logger.debug('user is not active.')
        # return self.GUEST
        if user.is_active:
            entry = ProjectUserBase.objects(project=self, user=user).first()
            if entry:
                if isinstance(entry, ProjectUser):
                    if entry.is_owner:
                        return self.ORGANIZER
                    elif entry.is_modeler:
                        return self.MODELER
                    elif entry.is_termer:
                        return self.TERM_MANAGER
                    else:
                        return self.MEMBER
                elif isinstance(entry, ProjectWaitingUserInbound):
                    return self.WAITING_MEMBER
        else:
            logger.debug('user is not active.')
        return self.GUEST

    def _get_grades(self, user):
        from erks.models import (
            ProjectUser,
            ProjectUserBase,
            ProjectWaitingUserInbound,
        )
        grades = []
        if user.is_active:
            entry = ProjectUserBase.objects(project=self, user=user).first()
            if isinstance(entry, ProjectUser):
                if entry.is_owner:
                    grades.append(self.ORGANIZER)
                if entry.is_modeler:
                    grades.append(self.MODELER)
                if entry.is_termer:
                    grades.append(self.TERM_MANAGER)
            if not grades:
                if isinstance(entry, ProjectUser):
                    grades.append(self.MEMBER)
                elif isinstance(entry, ProjectWaitingUserInbound):
                    grades.append(self.WAITING_MEMBER)
            if grades:
                return grades
        return [self.GUEST]

    def get_grades(self, user):
        def _(grade):
            return {
                'owner': {'label': 'label-primary', 'grade': gettext(u'프로젝트 관리자')},
                'member': {'label': 'label-warning', 'grade': gettext(u'일반회원')},
                'modeler': {'label': 'label-success', 'grade': gettext(u'모델러')},
                'termer': {'label': 'label-info', 'grade': gettext(u'용어 관리자')},
                'waiting_member': {'label': 'label-default', 'grade': gettext(u'손님(등록 대기중)')},
                'guest': {'label': 'label-default', 'grade': gettext(u'손님')}
            }[grade]
        return [_(grade) for grade in self._get_grades(user)]

    def check_to_enter(self, user=None):
        from erks.models import (
            ProjectUser,
        )
        '''project에 입장할 수 있는지를 검사'''
        if self.demo:
            return True

        # TODO: 이게 맞나요?
        if not current_user.is_active:
            return False

        if user is None:
            user = current_user._get_current_object()

        is_member = ProjectUser.objects(
            project=self, user=user).only('id').no_dereference().first() is not None
        return not self.private or is_member

    # def count_entities(self):
    #     from erks.erks_bps.erc.models import Entity
    #     return len(Entity.objects(prjId=str(self.id)))

    # def count_terms(self):
    #     from erks.erks_bps.term.models import Term
    #     return len(Term.objects(project=self))

    # def is_custom_img(self):
    #     return self.profile_imgf

    # def is_new(self):
    #     """
    #     project가 새 것인지를 판단하기
    #     주제영역이 하나라도 구성되어 있으면 알림을 주지 않기 위해.
    #     """
    #     from erks.erks_bps.erc.models import SubjectArea
    #     return SubjectArea.objects(prjId=str(self.id)).first() is None

    def get_profile_img_url(self, thumbnail=False):
        """binary값 기준으로 무작위로 profile image를 골라준다."""

        # 샘플이미지파일 개수
        SAMPLE_IMG_CNT = 5

        # TODO: 매번계산하므로 성능상 불리. 개선필요하다.
        random_number = sum(
            map(ord, list(hashlib.md5(self.id.binary).hexdigest()))
        ) % SAMPLE_IMG_CNT + 1
        if self.profile_imgf:
            return url_for('project.profile_img', project_id=self.id)
        else:
            if self.project_group and self.project_group.theme_key in THEME_KEYS:
                filename = '%01s/img/Project_thumb_768x573_%02d.jpg' % (self.project_group.theme_key, random_number)
            else:
                filename = 'img/r3/Project_thumb_768x573_%02d.jpg' % (random_number)
            return url_for('static', filename=filename)

    def destroy(self):
        '''project 삭제처리. project에 속한 모든 resource를 삭제하므로
        경우에 따라 heavy할 수 있기 때문에
        가급적이면 web-request에서 처리하지 않는 것을 권장'''

        from erks.erks_bps.erc.models import (
            Model,
            Domain,
            SubjectArea,
            Entity,
            Relation,
            Lock
        )

        # delete models
        Model.objects(prjId=str(self.id)).delete()

        # domain
        Domain.objects(prjId=str(self.id)).delete()

        # delete subjectarea
        SubjectArea.objects(prjId=str(self.id)).delete()

        # delete entities
        Entity.objects(prjId=str(self.id)).delete()

        # delete relation
        Relation.objects(prjId=str(self.id)).delete()

        # delete lock
        Lock.objects(prjId=str(self.id)).delete()

        # delete project
        self.delete()


class ProjectSummary(object):
    """project-home에서 보여주는 project정보요약"""

    @classmethod
    def get_erc_info(cls, project):
        """er-d information collector"""
        from erks.models import (
            Model,
            SubjectArea,
        )

        info_d = {}
        info_d['models_cnt'] = len(Model.head_objects(prjId=str(project.id)))
        info_d['subjects'] = [
            {
                'id': str(s['id']),
                'entities_count': len(s['entities']),
                'modified': s['modified'],
                'name': html_unescape(s['name']),
            } for s in SubjectArea.head_objects(
                prjId=str(project.id)
            ).order_by('name').limit(8) if 'entities' in s
        ]
        info_d['models'] = [
            {'id': str(s['id']),
             'name': str(s['name']),
             'entities_count': len(s['entities'])
             } for s in Model.head_objects(prjId=str(project.id))
        ]
        info_d['subjects_cnt'] = len(info_d['subjects'])
        info_d['entities_cnt'] = sum(map(
            lambda x: x['entities_count'],
            info_d['models']))
        info_d['terms_cnt'] = 0  # len(Term.objects(project=project))
        return info_d

    @classmethod
    def get_glossary_info(cls, project):
        """glossary information collector"""
        from erks.models import GlossaryBase, Glossary
        glossaries = [
            {
                'id': str(g['id']),
                'name': g.glossary_name,
                'strdterm_cnt': g.queryset_strdterm.count(),
                'unitterm_cnt': g.queryset_unitterm.count() if isinstance(g, Glossary) else 0,
                'infotype_cnt': g.queryset_infotype.count() if isinstance(g, Glossary) else 0,
                'domain_cnt': g.queryset_domainterm.count() if isinstance(g, Glossary) else 0,
                'modified_at': g['modified_at'],
                'is_gderived': not isinstance(g, Glossary),
                'obj': g,
            }
            for g in GlossaryBase.head_objects(project=project).order_by('-modified_at')
        ]
        info_d = {}
        info_d['glossaries'] = glossaries
        info_d['strdterm_cnt'] = sum(g['strdterm_cnt'] for g in glossaries)
        info_d['unitterm_cnt'] = sum(g['unitterm_cnt'] for g in glossaries)
        info_d['infotype_cnt'] = sum(g['infotype_cnt'] for g in glossaries)
        info_d['domain_cnt'] = sum(g['domain_cnt'] for g in glossaries)
        return info_d
