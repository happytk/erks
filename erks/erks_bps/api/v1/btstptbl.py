# -*- encoding:utf-8 -*-

# api(v1) specification

# /projectgroups
# /projectgroup/:slug
# /projectgroup/:slug/users
# /projectgroup/:slug/projects
# /projectgroup/:slug/glossaries
# /projectgroup/:slug/masterterms
# /projectgroup/:slug/mastertermrequests
# /projectgroup/:slug/entities
# /projectgroup/:slug/attirbutes
# /projectgroup/:slug/tables
# /projectgroup/:slug/columns
# /projectgroup/:slug/notices
# /projectgroup/:slug/qna

# /projects
# /project/:id
# /project/:id/users
# /project/:id/glossaries
# /project/:id/entities
# /project/:id/attirbutes
# /project/:id/tables
# /project/:id/columns


# /projectuser/:id
# /projectuser/:id/roles


# /glossaries
# /glossary/:id
# /glossary/:id/terms
# /glossary/:id/strdterms
# /glossary/:id/unitterms
# /glossary/:id/codeterms
# /glossary/:id/synonyms
# /glossary/:id/domains
# /glossary/:id/mydrafts
# /glossary/:id/codesets
# /glossary/:id/codeset/:csid
# /glossary/:id/infotypes
# /glossary/:id/infotype_upload_errors
# /glossary/:id/entities
# /glossary/:id/nonstrdterms
# /glossary/:id/draftterms
# /glossary/:id/reports

# /glossarymaster/:id
# /glossarymaster/:id/terms
# /glossarymaster/:id/termrequests
# /glossarymaster/:id/strdterms
# /glossarymaster/:id/unitterms
# /glossarymaster/:id/codeterms
# /glossarymaster/:id/synonyms
# /glossarymaster/:id/domains
# /glossarymaster/:id/mydrafts
# /glossarymaster/:id/codesets
# /glossarymaster/:id/codeset/:csid
# /glossarymaster/:id/infotypes
# /glossarymaster/:id/entities
# /glossarymaster/:id/draftterms
# /glossarymaster/:id/refcodeinstances

# /glossaryderived/:id
# /glossaryderived/:id/terms
# /glossaryderived/:id/termrequests
# /glossaryderived/:id/strdterms
# /glossaryderived/:id/unitterms
# /glossaryderived/:id/codeterms
# /glossaryderived/:id/synonyms
# /glossaryderived/:id/domains
# /glossaryderived/:id/mydrafts
# /glossaryderived/:id/codesets
# /glossaryderived/:id/codeset/:csid
# /glossaryderived/:id/infotypes
# /glossaryderived/:id/entities
# /glossaryderived/:id/nonstrdterms
# /glossaryderived/:id/draftterms

# /codesets

# /terms
# /term/:id
# /term/:id/codeinstances
# /term/:id/infotypes


# /termmasters
# /termmaster/:id
# /termmaster/:id/codeinstances
# /termmaster/:id/projectcodeinstances
# /termmaster/:id/infotypes


# /codeterm/:id/codeinstances


# /model/:id/entities

# /users
# /user/:id
# /user/:id/projects
# /user/:id/myprojects
# /user/:id/visitedprojects
from mongoengine import Q
from itertools import islice
from bson import ObjectId
from flask import g, jsonify, current_app, request, abort
from flask import Blueprint
from flask_login import current_user
# from flask_restful import Api, Resource
from flask.views import MethodView as Resource
from ercc.models import (
    CodeSet,
    CodeTerm,
    CodeTermMaster,
    Glossary,
    GlossaryMaster,
    GlossaryDerived,
    Model,
    SubjectArea,
    NonStrdTerm,
    NonStrdTermMap,
    Entity,
    Project,
    ProjectGroup,
    ProjectGroupNotice,
    ProjectGroupQnA,
    ProjectUser,
    StrdTerm,
    StrdTermMaster,
    Term,
    TermMasterRequest,
    UnitTerm,
    UnitTermMaster,
    User,
    ModelSchemaDiff,
)
from ercc.ercc_bps.schema.models import (
    SchemaCollector,
    SchemaCollectResult,
    Schema
)
from ercc.ercc_bps.erc.models import ProjectERD
from ercc.ercc_bps.projectuser.forms import (
    ProjectUserGlossariesForm,
    ProjectUserModelsForm,
)
from ercc.ercc_bps.glossarymaster.forms import (
    TermMasterAdvSearchForm,
    TermMasterDerivedAdvSearchForm,
)
from ercc.ercc_bps.api.v1 import (
    api_gen,
    ListResource,
    # GenResource,
    SingleResource,
    SingleListResource,
    SingleGenResource,
)
import json

API_PREFIX = '/api_btstptbl'

# /projectgroups
# /projectgroup/:slug
# /projectgroup/:slug/users
# /projectgroup/:slug/projects
# /projectgroup/:slug/glossaries
# /projectgroup/:slug/masterterms
# /projectgroup/:slug/mastertermrequests
# /projectgroup/:slug/entities
# /projectgroup/:slug/notices
# /projectgroup/:slug/qna


class ProjectGroupListResource(ListResource):
    '''projectgroup의 목록'''
    resource_cls = ProjectGroup
    input_cls = None


class ProjectGroupResource(SingleResource):
    '''projectgroup 개별 정보'''
    resource_cls = ProjectGroup
    input_cls = ProjectGroup

    def get(self, id):
        '''slug기준으로 검색해야 해서 SingleResource의 get을 사용할 수 없음'''
        queryset = self.resource_cls.objects
        if self.exclude_fields:
            queryset = queryset.exclude(*self.exclude_fields)
        return jsonify(
            json.loads(queryset.get_or_404(slug=id).to_json()))


class ProjectGroupUsersResource(SingleListResource):
    '''projectgroup에 등록된 사용자 목록,
    search: email문자의 포함여부를 검색'''
    input_cls = ProjectGroup

    def queryset(self, id):
        self.project_group = ProjectGroup.objects.get_or_404(slug=id)
        return self.project_group.queryset_member

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(user_email__icontains=search_string)
        )


class ProjectGroupProjectsResource(SingleListResource):
    '''projectgroup에 등록된 프로젝트 목록,
    search: email문자의 포함여부를 검색'''
    dynamic_fields = ["url"]
    input_cls = ProjectGroup

    def queryset(self, id):
        self.project_group = ProjectGroup.objects.get_or_404(slug=id)
        return self.project_group.queryset_project

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(Q(title__icontains=search_string))


class ProjectGroupGlossariesResource(SingleListResource):
    '''projectgroup에 등록된 프로젝트 용어사전 목록(전사용어사전을 제외한)'''
    dynamic_fields = ['url']
    input_cls = ProjectGroup

    def queryset(self, id):
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        return project_group.queryset_glossary.filter(
            _cls__ne='Glossary.GlossaryMaster'
        )


class ProjectGroupMasterTermsResource(SingleListResource):
    '''projectgroup에 등록된 전사용어 목록'''
    dynamic_fields = ['url']
    input_cls = ProjectGroup

    def queryset(self, id):
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        return project_group.queryset_master_term


class ProjectGroupMasterTermRequestsResource(SingleListResource):
    '''projectgroup에서 신청중 전사용어 목록'''
    dynamic_fields = ['url']
    input_cls = ProjectGroup

    def queryset(self, id):
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        return project_group.queryset_master_term_request


class ProjectGroupEntitiesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)
        prj_ids = [
            str(p.id)
            for p in Project.objects(project_group=pg).only('id')
        ]

        yield from (
            rsc.to_json(indent=False, ensure_ascii=False)
            for rsc in Entity.objects(
                entTyp__ne='P',
                prjId__in=prj_ids,
                entNm__icontains=search
            ).skip(offset).limit(limit)
        )


class ProjectGroupTablesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)
        prj_ids = [
            str(p.id)
            for p in Project.objects(project_group=pg).only('id')
        ]

        yield from (
            rsc.to_json(indent=False, ensure_ascii=False)
            for rsc in Entity.objects(
                entTyp__ne='P',
                prjId__in=prj_ids,
                tabNm__icontains=search
            ).skip(offset).limit(limit)
        )


class ProjectGroupAttributesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '-')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)
        prj_ids = [
            str(p.id)
            for p in Project.objects(project_group=pg).only('id')
        ]

        def _patch(d, entity):
            '''d에 entity정보를 patch'''
            d['prjId'] = getattr(entity, 'prjId', '0' * 24)
            prj = Project.objects(id=ObjectId(d['prjId'])).first()
            d['prjNm'] = prj.title if prj else ''
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            model = Model.objects(
                entities=str(entity.id), newest='Y'
            ).only('name').first()
            d['modelNm'] = model.name if model else ''
            d['modelOid'] = str(model.Oid) if model else ''
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(attr.get('Lattr', {}), entity),
                    ensure_ascii=False,
                    indent=True
                )
                for entity in Entity.objects(
                    entTyp__ne='P',
                    prjId__in=prj_ids
                )
                for attr in entity.attrs
                if search in attr.get('Lattr', {}).get('attrNm', '')
            ),
            offset,
            limit,
        )


class ProjectGroupPropertiesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)
        prj_ids = [
            str(p.id)
            for p in Project.objects(project_group=pg).only('id')
        ]

        def _patch(d, entity):
            '''d에 entity정보를 patch'''
            d['prjId'] = getattr(entity, 'prjId', '0' * 24)
            prj = Project.objects(id=ObjectId(d['prjId'])).first()
            d['prjNm'] = prj.title if prj else ''
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            model = Model.objects(
                entities=str(entity.id), newest='Y'
            ).only('name').first()
            d['modelNm'] = model.name if model else ''
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(attr.get('Pattr', {}), entity),
                    ensure_ascii=False,
                    indent=True
                )
                for entity in Entity.objects(
                    entTyp__ne='P',
                    prjId__in=prj_ids
                )
                for attr in entity.attrs
                if search in attr.get('Pattr', {}).get('attrNm', '')
            ),
            offset,
            limit,
        )


class ProjectGroupSubjectareasResource(Resource):
    def get(self, **kwargs):
        id = kwargs.get('id')
        # subj_id = kwargs.get('subjId')
        # subjectarea_id = request.args.get('subjId', '')
        # entity_name = request.args.get('entNm', '')
        # attribute_name = request.args.get('attrNm', '')

        pg = ProjectGroup.objects.get_or_404(slug=id)

        def patchSubjectareaInfo(mdl_object, prj_id):
            per = ProjectErdLinkResource()
            subjectareas = [
                {
                    "subjNm": SubjectArea.objects(id=ObjectId(s_ids["id"])).first().name,
                    "subjOid": s_ids["Oid"],
                    "url": per.get_text_url(id=prj_id, subjId=s_ids["Oid"])
                }
                for s_ids in mdl_object["subjectareas"]
            ]
            return subjectareas

        def patchModelInfo(prj_id):
            models = [
                {
                    'mdlNm': m["name"],
                    "mdlOid": str(m["Oid"]),
                    "subjectareas": patchSubjectareaInfo(mdl_object=m, prj_id=prj_id)
                }
                for m in Model.objects(newest='Y', prjId=str(prj_id))
            ]
            return models

        def patchProjectInfo(prj_id):
            prj = Project.objects(id=ObjectId(prj_id)).first()
            project_info = {"prjId": str(prj_id), "prjNm": prj.title}
            project_info["models"] = patchModelInfo(prj_id)
            return project_info

        pgSubjectareas = [
            patchProjectInfo(p.id)
            for p in Project.objects(project_group=pg).only('id')
        ]

        return jsonify(pgSubjectareas)


class ProjectGroupNoticesResource(SingleListResource):
    '''projectgroup에 등록된 공지사항 목록'''
    input_cls = ProjectGroup
    resource_cls = ProjectGroupNotice

    def queryset(self, id):
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        return ProjectGroupNotice.objects(project_group=project_group.id, use_yn=True)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(title__icontains=search_string)
            # Q(contents__icontains=search_string)
        )


class ProjectGroupQnAResource(SingleListResource):
    '''projectgroup에 등록된 QnA 목록'''
    input_cls = ProjectGroup

    def queryset(self, id):
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        return ProjectGroupQnA.objects(project_group=project_group.id, use_yn=True)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(title__icontains=search_string)
            # Q(contents__icontains=search_string)
        )

# /projects
# /project/:id
# /project/:id/users
# /project/:id/users/advsearch
# /project/:id/user/:user_id
# /project/:id/glossaries
# /project/:id/entities
# /project/:id/attirbutes
# /project/:id/tables
# /project/:id/columns


class ProjectListResource(ListResource):
    '''전체 project 목록'''
    exclude_fields = ['project_group', 'is_free']
    resource_cls = Project
    input_cls = None


class ProjectResource(SingleResource):
    '''project 개별 목록'''
    resource_cls = Project
    input_cls = Project


class ProjectUsersResource(SingleListResource):
    '''project내 사용자 목록'''

    exclude_fields = ['project', 'project_group_user']
    input_cls = Project

    def queryset(self, id):
        self.project = Project.objects.only('id').get_or_404(id=id)
        return self.project.queryset_project_user

    def response_headers(self):
        return {
            'X-Current-User-Project-Grade': self.project._get_grades(
                current_user._get_current_object()),
        }

    def search(self, query, search_string):
        return query.filter(Q(user_email__icontains=search_string))
        return query


class ProjectUsersAdvSearch(SingleListResource):
    '''project내 사용자 목록(상세검색용)'''

    exclude_fields = ['project', 'project_group_user']
    dynamic_fields = ['is_ongoing', 'is_referred']
    input_cls = Project

    def queryset(self, id):
        from ercc.ercc_bps.project.forms import SearchMemberForm

        project = Project.objects.get_or_404(id=id)
        form = SearchMemberForm.from_json(request.args)
        if form.validate():
            search_q = form.search()
            return project.queryset_project_user.filter(**search_q)
        else:
            current_app.logger.debug(form.errors)
            abort(400)  # todo: check error number


class ProjectGlossariesResource(SingleListResource):
    '''project내 용어사전 목록'''

    input_cls = Project

    def queryset(self, id):
        project = Project.objects.only('id').get_or_404(id=id)
        return project.queryset_glossary


class ProjectErdLinkResource(Resource):
    def get(self, **kwargs):
        id = kwargs.get('id')
        subjectarea_id = request.args.get('subjId', '')
        entity_name = request.args.get('entNm', '')
        attribute_name = request.args.get('attrNm', '')

        from ercc.ercc_bps.erc.models import ProjectERD

        prj_erd = ProjectERD(id)
        url = {"url": prj_erd.url(subjId=subjectarea_id, entNm=entity_name, attrNm=attribute_name)}
        return jsonify(url)

    def get_text_url(self, **kwargs):
        id = kwargs.get('id')
        subjectarea_id = kwargs.get('subjId')

        # subjectarea_id = request.args.get('subjId', '')
        entity_name = request.args.get('entNm', '')
        attribute_name = request.args.get('attrNm', '')
        prj_erd = ProjectERD(id)

        return prj_erd.url(subjId=subjectarea_id, entNm=entity_name, attrNm=attribute_name)


"""
class ProjectSchemaCollectorsResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        # search = kwargs.get('search')
        id = kwargs.get('id')

        project = Project.objects.get_or_404(id=id)
        yield from (
            rsc.to_json(indent=False, ensure_ascii=False)
            for rsc in SchemaCollector.objects(
                project=project.id
            ).skip(offset).limit(limit)
        )
"""


class ProjectSchemaCollectorsResource(SingleListResource):

    input_cls = Project
    resource_cls = SchemaCollector

    def queryset(self, id):
        project = Project.objects.only('id').get_or_404(id=id)
        return SchemaCollector.objects(project=project)


class ProjectModelHistoryResource(Resource):
    def get(self, **kwargs):
        id = kwargs.get('id')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        import datetime

        try:
            date_from = datetime.datetime.strptime(date_from, "%Y%m%d")
        except:
            date_from = None

        try:
            date_to = datetime.datetime.strptime(date_to, "%Y%m%d")
        except:
            date_to = None

        return jsonify(self.get_history_list(project_id=id, date_from=date_from, date_to=date_to))

    def get_history_list(self, project_id, date_from=None, date_to=None):
        from ercc.ercc_bps.erc.models import ModelHistory

        history_queryset = ModelHistory.objects(project_id=project_id)
        # history_queryset = history_queryset(Q(modified__gte=date_from, modified__lt=date_to))

        if date_from:
            history_queryset = history_queryset.filter(modified__gte=date_from)
        if date_to:
            history_queryset = history_queryset.filter(modified__lt=date_to)

        # history_queryset = history_queryset(Q(modified__gte=date_from, modified__lt=date_to))
        return [
            dtl
            for dtl in history_queryset
        ]


class ProjectEntitiesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search')
        id = kwargs.get('id')

        project = Project.objects.get_or_404(id=id)
        yield from (
            rsc.to_json(indent=False, ensure_ascii=False)
            for rsc in Entity.objects(
                entTyp__ne='P',
                prjId=str(project.id),
                entNm__icontains=search
            ).skip(offset).limit(limit)
        )


class ProjectTablesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search')
        id = kwargs.get('id')

        project = Project.objects.get_or_404(id=id)
        yield from (
            rsc.to_json(indent=False, ensure_ascii=False)
            for rsc in Entity.objects(
                entTyp__ne='P',
                prjId=str(project.id),
                tabNm__icontains=search
            ).skip(offset).limit(limit)
        )


class ProjectAttributesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '-')
        id = kwargs.get('id')

        project = Project.objects.get_or_404(id=id)

        def _patch(d, entity):
            '''d에 entity정보를 patch'''
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            model = Model.objects(
                entities=str(entity.id), newest='Y'
            ).only('name').first()
            d['modelNm'] = model.name if model else ''
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(attr.get('Lattr', {}), entity),
                    ensure_ascii=False,
                    indent=True
                )
                for entity in Entity.objects(
                    entTyp__ne='P',
                    prjId=str(project.id)
                )
                for attr in entity.attrs
                if search in attr.get('Lattr', {}).get('attrNm', '')
            ),
            offset,
            limit,
        )


class ProjectPropertiesResource(SingleGenResource):
    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '')
        id = kwargs.get('id')

        project = Project.objects.get_or_404(id=id)

        def _patch(d, entity):
            '''d에 entity정보를 patch'''
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            model = Model.objects(
                entities=str(entity.id), newest='Y'
            ).only('name').first()
            d['modelNm'] = model.name if model else ''
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(attr.get('Pattr', {}), entity),
                    ensure_ascii=False,
                    indent=True
                )
                for entity in Entity.objects(
                    entTyp__ne='P',
                    prjId=str(project.id)
                )
                for attr in entity.attrs
                if search in attr.get('Pattr', {}).get('attrNm', '')
            ),
            offset,
            limit,
        )


# /schemacollector/:id/resultlist
# /schemacollector/:id/schema


class SchemaCollectResultListResource(SingleListResource):
    input_cls = SchemaCollector
    # resource_cls = SchemaCollectResult

    def queryset(self, collector_id):
        return SchemaCollectResult.objects(schema_collector=ObjectId(collector_id))


class SchemaCollectResultResource(SingleListResource):
    def queryset(self, schema_collect_result_id):
        return Schema.objects(
            schema_collect_result=ObjectId(schema_collect_result_id)
        )


# /projectuser/:id
# /projectuser/:id/glossaries
# /projectuser/:id/models

class ProjectUserResource(SingleResource):
    '''project-user관계정보'''
    resource_cls = ProjectUser
    input_cls = ProjectUser


class ProjectUserGlossariesResource(Resource):
    '''project-user의 project-glossaries 관계정보
    (project-glossaries에서 자신의 것을 구분 표기해주는 정보 생성)'''
    input_cls = ProjectUser

    def get(self, id):
        pu = ProjectUser.objects.get_or_404(id=id)

        # temporary new fields for json-output
        glossaries = ', '.join(
            obj.to_json()
            for obj in Glossary.head_objects(
                project=pu.project).only('glossary_name').all())
        glossaries = json.loads('[{}]'.format(glossaries))
        mg_ids = [str(g.id) for g in pu.manageable_glossaries]
        for glossary in glossaries:
            glossary["is_my_glossary"] = glossary["id"] in mg_ids

        return jsonify(glossaries)

    def post(self, id):
        pu = ProjectUser.objects.get_or_404(id=id)
        form = ProjectUserGlossariesForm(request.form)
        if form.validate():
            form.populate_obj(pu)
            pu.save()
            return self.get(id)
        else:
            abort(400)


class ProjectUserModelsResource(Resource):
    '''project-user의 project-models 관계정보
    (project-models에서 자신의 것을 구분 표기해주는 정보 생성)'''
    input_cls = ProjectUser

    def get(self, id):
        pu = ProjectUser.objects.get_or_404(id=id)

        # temporary new fields for json-output
        models = ', '.join(
            obj.to_json()
            for obj in Model.head_objects(
                prjId=str(pu.project.id)).only('name').all())
        models = json.loads('[{}]'.format(models))

        '''manageable_models 항상 root_object를 가지고 있기 때문에
        head_object를 조회후에 Oid를 비교해서 my_model을 판단'''
        mm_ids = [str(g.id) for g in pu.manageable_models]
        for model in models:
            model["is_my_model"] = model["Oid"] in mm_ids

        return jsonify(models)

    def post(self, id):
        pu = ProjectUser.objects.get_or_404(id=id)
        form = ProjectUserModelsForm(request.form)
        if form.validate():
            form.populate_obj(pu)
            pu.save()
            return self.get(id)
        else:
            abort(400)


# /glossaries
# /glossary/:id
# /glossary/:id/terms
# /glossary/:id/strdterms
# /glossary/:id/unitterms
# /glossary/:id/codeterms
# /glossary/:id/synonyms
# /glossary/:id/domains
# /glossary/:id/mydrafts
# /glossary/:id/codesets
# /glossary/:id/codeset/:csid
# /glossary/:id/infotypes
# /glossary/:id/infotype_upload_errors
# /glossary/:id/entities
# /glossary/:id/draftterms
# /glossary/:id/reports


class GlossaryListResource(ListResource):
    '''전체 용어사전 목록'''
    resource_cls = Glossary
    input_cls = None


class GlossaryResource(SingleResource):
    '''개별 용어사전 정보'''
    resource_cls = Glossary
    input_cls = Glossary


class GlossaryTermsResource(SingleListResource):
    '''용어사전의 용어 목록
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'code_instances',
        'composition',
        'created_by',
        # 'domain',
        'glossary',
        'infotypes',
        'modified_by',
        'project',
        'published_by',
        'requested_by',
    ]
    dynamic_fields = ['is_ongoing', 'is_referred']
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        # return Term.all_objects(
        #     glossary=glossary,
        #     project=glossary.project,
        #     project_group=glossary.project.project_group)
        return glossary.queryset_term

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(Q(term_name__icontains=search_string))


class GlossaryTermsAdvSearch(SingleListResource):
    '''용어사전의 용어 목록 - 상세검색용
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'code_instances',
        'composition',
        'created_by',
        # 'domain',
        'glossary',
        'infotypes',
        'modified_by',
        'project',
        'published_by',
        'requested_by',
    ]
    dynamic_fields = [
        'is_ongoing',
        'is_referred',
        'url',
        'update_url',
    ]
    input_cls = Glossary

    def queryset_advsearch(self, id, args):
        g.glossary = Glossary.head_objects.get_or_404(id=id)
        g.project = g.glossary.project
        g.project_group = g.glossary.project_group

        AdvSearchFormCls = g.glossary.adv_search_form_cls()
        form = AdvSearchFormCls.from_json(args)
        if form.validate():
            return form.queryset_search
        else:
            current_app.logger.debug(form.errors)
            abort(400)  # todo: check error number

    def queryset(self, id):
        return self.queryset_advsearch(id, request.args)


class GlossaryStrdtermsResource(SingleListResource):
    '''용어사전의 표준용어 목록
    (일반프로젝트 소속의 용어사전대상)'''
    exclude_fields = [
        'created_by',
        'glossary',
        'modified_by',
        'project',
        'published_by',
        'rep_infotype',
        'requested_by',
    ]
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_strdterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryUnittermsResource(SingleListResource):
    '''용어사전의 단위용어 목록
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'created_by',
        'glossary',
        'infotypes',
        'modified_by',
        'project',
        'published_by',
        'rep_infotype',
        'requested_by',
    ]
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_unitterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string) |
            Q(physical_term_fullname__icontains=search_string)
        )


class GlossaryDrafttermsResource(SingleListResource):
    '''용어사전의 신청중인 용어 목록
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'created_by',
        'glossary',
        'infotypes',
        'modified_by',
        'project',
        'published_by',
        'rep_infotype',
        'requested_by',
    ]
    dynamic_fields = [
        'url',
    ]
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_draftterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryMyDrafttermsResource(SingleListResource):
    '''용어사전의 나의 신청중인 용어 목록
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'created_by',
        'glossary',
        'infotypes',
        'modified_by',
        'project',
        'published_by',
        'rep_infotype',
        'requested_by',
    ]
    dynamic_fields = [
        'url',
    ]
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_mydraftterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryCodetermsResource(SingleListResource):
    '''용어사전의 코드용어 목록
    (일반프로젝트 소속의 용어사전대상)'''

    exclude_fields = [
        'created_by',
        'glossary',
        'modified_by',
        'project',
        'published_by',
        'requested_by',
    ]
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        # return StrdTerm.objects(glossary=glossary, is_code=True)
        return glossary.queryset_codeterm

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryNormalCodetermsResource(GlossaryCodetermsResource):
    '''용어사전의 코드용어(일반코드) 목록
    (일반프로젝트 소속의 용어사전대상)'''
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_codeterm.filter(code_type='NORMAL')
        # return StrdTerm.objects(
        #     glossary=glossary,
        #     is_code=True,
        #     code_type='NORMAL')


class GlossaryInfotyesResource(SingleListResource):
    '''용어사전의 인포타입 목록
    (일반프로젝트 소속의 용어사전대상)'''
    input_cls = Glossary

    # exclude_fields = ['glossary', 'project']
    dynamic_fields = [
        'delete_url',
        # 'humanize_logical_type',
        'is_referred',
        'update_url',
    ]

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_infotype
        # return InfoType.objects(
        #     glossary=glossary,
        #     project=glossary.project)
        # project_group=glossary.project.project_group)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(infotype_name__icontains=search_string) |
            Q(logical_type__icontains=search_string)
            # Q(humanized_logical_type__icontains=search_string)
            # Q(decimal_place__icontains=search_string)
        )


class GlossaryReportsResource(SingleListResource):
    '''용어사전리포트'''
    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_report.only(
            'created_at',
            'glossary',
            'status',
            'strdterm_count',
            'codeterm_count',
            'synonym_count',
            'infotype_count',
            'unitterm_count',
            'domain_count',
            'invalid_strdterm_count',
            'invalid_unitterm_count',
            'invalid_synonym_count',
            'invalid_infotype_count',
            'dup_term_name_count',
            'dup_physical_term_name_count',
            'invalid_composition_count',
        )


# /glossarymaster/:id
# /glossarymaster/:id/terms
# /glossarymaster/:id/terms/advsearch
# /glossarymaster/:id/strdterms
# /glossarymaster/:id/unitterms
# /glossarymaster/:id/codeterms
# /glossarymaster/:id/synonyms
# /glossarymaster/:id/domains
# /glossarymaster/:id/mydrafts
# /glossarymaster/:id/codesets
# /glossarymaster/:id/codeset/:csid
# /glossarymaster/:id/infotypes
# /glossarymaster/:id/entities
# /glossarymaster/:id/draftterms


class GlossaryMasterStrdtermsResource(SingleListResource):
    '''전사용어사전의 표준용어 목록'''

    exclude_fields = [
        'created_by',
        'modified_by',
        'glossary_master',
        'project_group',
        'rep_infotype',
    ]
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary = GlossaryMaster.objects.get_or_404(id=id)
        return glossary.queryset_strdterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryMasterUnittermsResource(SingleListResource):
    '''전사용어사전의 단위용어 목록'''

    exclude_fields = [
        'created_by',
        'modified_by',
        'glossary_master',
        'infotypes',
        'project_group',
        'rep_infotype',
    ]
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary = GlossaryMaster.objects.get_or_404(id=id)
        return glossary.queryset_unitterm
        # return UnitTerm.objects(glossary=glossary)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string) |
            Q(physical_term_fullname__icontains=search_string)
        )


class GlossaryMasterInfotypesResource(SingleListResource):
    '''전사용어사전의 인포타입 목록'''

    exclude_fields = [
        'glossary_master',
        'project_group',
    ]
    dynamic_fields = [
        'delete_url',
        # 'humanize_logical_type',
        'is_referred',
        'update_url',
    ]
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary = GlossaryMaster.objects.get_or_404(id=id)
        return glossary.queryset_infotype
        # return InfoType.objects(
        #     glossary=glossary,
        #     project=glossary.project)
        # project_group=glossary.project.project_group)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(infotype_name__icontains=search_string)
            # Q(humanized_logical_type__icontains=search_string)
        )


class GlossaryMasterTermsAdvSearchResource(SingleListResource):
    '''전사용어사전의 용어(상세검색) 목록'''

    exclude_fields = [
        # 'code_instances',
        'composition',
        'created_by',
        # 'domain',
        'glossary_master',
        'infotypes',
        'modified_by',
        'project_group',
    ]
    dynamic_fields = [
        'is_referred',
        'url',
        'delete_url',
        'update_url',
    ]
    input_cls = GlossaryMaster

    def queryset_advsearch(self, id, args):

        glossary_master = GlossaryMaster.objects.get_or_404(id=id)
        form = TermMasterAdvSearchForm.from_json(
            args, glossary_master=glossary_master)
        if form.validate():
            return form.queryset_search
        else:
            current_app.logger.debug(form.errors)
            abort(400)  # todo: check error number

    def queryset(self, id):
        return self.queryset_advsearch(id, request.args)


class GlossaryMasterTermRequestsResource(SingleListResource):
    '''전사용어사전의 용어(상세검색) 목록'''
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary_master = GlossaryMaster.objects.get_or_404(id=id)
        return TermMasterRequest.objects(
            glossary_master=glossary_master, done=False)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string)
        )


class GlossaryMasterTermRequestsDoneResource(SingleListResource):
    '''전사용어사전의 용어(상세검색) 목록'''
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary_master = GlossaryMaster.objects.get_or_404(id=id)
        return TermMasterRequest.objects(
            glossary_master=glossary_master, done=True)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string)
        )


class GlossaryMasterCodeTermsResource(SingleListResource):
    '''전사용어사전의 코드용어 목록'''

    dynamic_fields = [
        'code_instance_count',
        'update_url',
        'delete_url',
    ]
    input_cls = GlossaryMaster

    def queryset(self, id):
        glossary_master = GlossaryMaster.objects.get_or_404(id=id)
        return CodeTermMaster.objects(
            glossary_master=glossary_master)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string) |
            Q(logical_data_type__icontains=search_string) |
            Q(code_id__icontains=search_string)
        )


# /glossaryderived/:id
# /glossaryderived/:id/terms
# /glossaryderived/:id/termrequests
# /glossaryderived/:id/strdterms
# /glossaryderived/:id/unitterms
# /glossaryderived/:id/codeterms
# /glossaryderived/:id/synonyms
# /glossaryderived/:id/domains
# /glossaryderived/:id/mydrafts
# /glossaryderived/:id/codesets
# /glossaryderived/:id/codeset/:csid
# /glossaryderived/:id/infotypes
# /glossaryderived/:id/entities
# /glossaryderived/:id/nonstrdterms
# /glossaryderived/:id/draftterms
# /glossaryderived/:id/reports

class GlossaryDerivedTermsAdvSearchResource(SingleListResource):
    exclude_fields = [
        # 'code_instances',
        'composition',
        'created_by',
        # 'domain',
        'glossary_master',
        # 'infotypes',
        # 'modified_by',
        'project_group',
    ]
    dynamic_fields = [
        'is_referred',
        'url',
    ]
    input_cls = GlossaryDerived

    def queryset(self, id):
        glossary_derived = GlossaryDerived.head_objects.get_or_404(id=id)
        form = TermMasterDerivedAdvSearchForm.from_json(
            request.args, glossary_derived=glossary_derived)
        if form.validate():
            return form.queryset_search
        else:
            current_app.logger.debug(form.errors)
            abort(400)  # todo: check error number

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryDerivedTermRequestsResource(SingleListResource):

    input_cls = GlossaryDerived

    def queryset(self, id):
        glossary_derived = GlossaryDerived.head_objects.get_or_404(id=id)
        return TermMasterRequest.objects(
            glossary_derived=glossary_derived)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string)
        )


class GlossaryDerivedCodeTermsResource(SingleListResource):
    dynamic_fields = [
        'code_instance_count',
        'update_url',
        'delete_url',
    ]
    input_cls = GlossaryDerived
    resource_cls = CodeTerm

    def queryset(self, id):
        glossary_derived = \
            GlossaryDerived.head_objects.get_or_404(id=id)
        return CodeTerm.objects(
            glossary_derived=glossary_derived)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string) |
            Q(logical_data_type__icontains=search_string) |
            Q(code_id__icontains=search_string)
        )


class GlossaryDerivedNonStrdTermsResource(SingleListResource):
    input_cls = GlossaryDerived
    resource_cls = NonStrdTerm

    def queryset(self, id):
        glossary_derived = \
            GlossaryDerived.head_objects.get_or_404(id=id)
        return NonStrdTerm.objects(
            glossary=glossary_derived)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(logical_name__icontains=search_string) |
            Q(logical_type__icontains=search_string) |
            Q(physical_name__icontains=search_string) |
            Q(physical_type__icontains=search_string)
        )
    # def get(self, id):
    #     glossary_derived = \
    #         GlossaryDerived.head_objects.get_or_404(id=id)

    #     # args
    #     offset = int(request.args.get('offset', 0))
    #     limit = int(request.args.get('limit', 10))
    #     sorted_ = request.args.get('sort', '')  # +field1,-field2
    #     order = request.args.get('order', 'asc')
    #     search = request.args.get('search', '')  # unified_search_text

    #     attrs = glossary_derived.context_nonstrdterm(search)

    #     if sorted_ and attrs:
    #         # None 은 비교가 안되므로 강제 문자열처리
    #         attrs.sort(key=lambda x: str(getattr(x, sorted_, '')))
    #         if order == 'desc':
    #             attrs.reverse()

    #     gen = (
    #         obj
    #         for obj in attrs[offset:offset + limit]
    #     )

    #     headers = {
    #         'X-Total-Count': len(attrs),
    #         # 'X-Total-Pages': int(total_count / page_size),
    #     }
    #     headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
    #     return current_app.response_class(
    #         api_gen(gen, total=len(attrs)),
    #         headers=headers,
    #         mimetype='application/json')


class GlossaryDerivedNonStrdTermMapsResource(SingleListResource):
    dynamic_fields = [
        'update_url',
        'delete_url',
    ]
    input_cls = GlossaryDerived

    def queryset(self, id):
        glossary_derived = \
            GlossaryDerived.head_objects.get_or_404(id=id)
        return NonStrdTermMap.objects(
            glossary_derived=glossary_derived)

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )


class GlossaryDerivedNormalCodeTermsResource(SingleListResource):
    dynamic_fields = [
        'code_instance_count',
        'update_url',
        'delete_url',
    ]
    input_cls = GlossaryDerived

    def queryset(self, id):
        glossary = GlossaryDerived.head_objects.get_or_404(id=id)
        return glossary.queryset_codeterm.filter(code_type='NORMAL')


class GlossaryDerivedReportsResource(SingleListResource):
    input_cls = GlossaryDerived

    def queryset(self, id):
        glossary = GlossaryDerived.head_objects.get_or_404(id=id)
        return glossary.queryset_report


# /codesets


class CodeSetListResource(SingleListResource):
    resource_cls = CodeSet
    input_cls = CodeSet


# /codeterm/:id/codeinstnaces

class CodeTermCodeInstancesResource(Resource):
    input_cls = CodeTerm

    def get(self, id):
        '''codeinstances는
        queryset이 아니라 embeddedfieldlist이므로 직접구현'''

        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        sorted_ = request.args.get('sort', '')  # +field1,-field2
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text

        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()

        strdterm = CodeTerm.objects.get_or_404(id=id)
        code_instances = strdterm.virtual_code_instances

        if sorted_ and code_instances:
            # None 은 비교가 안되므로 강제 문자열처리
            code_instances.sort(key=lambda x: str(getattr(x, sorted_)))
            if order == 'desc':
                code_instances.reverse()

        if search:
            code_instances = [
                c for c in code_instances
                if c.inst_value.find(search) >= 0 or
                c.inst_definition.find(search) >= 0 or
                c.inst_description.find(search) >= 0 or
                c.inst_remark.find(search) >= 0]

        gen = (
            json.loads(obj.to_json())
            for obj in code_instances[offset:offset + limit]
        )

        headers = {
            'X-Total-Count': len(code_instances),
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            api_gen(gen, total=len(code_instances)),
            headers=headers,
            mimetype='application/json')

# /term/:id
# /term/:id/codeinstances
# /term/:id/infotypes


class TermResource(SingleResource):
    resource_cls = Term
    input_cls = Term


class TermCodeInstancesResource(Resource):
    input_cls = StrdTerm

    def get(self, id):
        '''codeinstances는
        queryset이 아니라 embeddedfieldlist이므로 직접구현'''

        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        sorted_ = request.args.get('sort', '')  # +field1,-field2
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text

        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()

        strdterm = StrdTerm.objects.get_or_404(id=id)
        code_instances = strdterm.virtual_code_instances

        if sorted_ and code_instances:
            # None 은 비교가 안되므로 강제 문자열처리
            code_instances.sort(key=lambda x: str(getattr(x, sorted_)))
            if order == 'desc':
                code_instances.reverse()

        if search:
            code_instances = [
                c for c in code_instances
                if c.inst_value.find(search) >= 0 or
                c.inst_definition.find(search) >= 0 or
                c.inst_description.find(search) >= 0 or
                c.inst_remark.find(search) >= 0
            ]

        gen = (
            json.loads(obj.to_json())
            for obj in code_instances[offset:offset + limit]
        )
        headers = {
            'X-Total-Count': len(code_instances),
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            api_gen(gen, total=len(code_instances)),
            headers=headers,
            mimetype='application/json')


class TermInfotypesResource(Resource):
    input_cls = UnitTerm

    def get(self, id):
        '''queryset이 아니라 embeddedfieldlist이므로 직접구현'''

        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        sorted_ = request.args.get('sort', '')  # +field1,-field2
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text

        # current_app.logger.debug(request.args)

        unitterm = self.input_cls.objects.only('infotypes').get_or_404(id=id)
        infotypes = unitterm.infotypes

        if sorted_ and infotypes:
            # None 은 비교가 안되므로 강제 문자열처리
            infotypes.sort(key=lambda x: str(getattr(x, sorted_)))
            if order == 'desc':
                infotypes.reverse()

        if search:
            infotypes = [
                infotype
                for infotype in infotypes
                if (
                    infotype.infotype_name.find(search) >= 0 or
                    infotype.logical_type.find(search) >= 0
                )
            ]
        gen = (
            json.loads(obj.to_json())
            for obj in infotypes[offset:offset + limit]
        )
        headers = {
            'X-Total-Count': len(infotypes),
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            api_gen(gen, total=len(infotypes)),
            headers=headers,
            mimetype='application/json')


# /termmasters
# /termmaster/:id
# /termmaster/:id/codeinstances
# /termmaster/:id/projectcodeinstances
# /termmaster/:id/infotypes

class TermMasterInfotypesResource(TermInfotypesResource):
    input_cls = UnitTermMaster


class TermMasterProjectCodeInstancesResource(SingleListResource):
    input_cls = StrdTermMaster

    def get(self, id):
        '''codeinstances는
        queryset이 아니라 embeddedfieldlist이므로 직접구현'''

        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        sorted_ = request.args.get('sort', '')  # +field1,-field2
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text

        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()
        strdterm_master = StrdTermMaster.objects.get_or_404(id=id)
        # 마스터 기준으로 일반 프로젝트의 CodeTerm을 검색
        codeterms = CodeTerm.objects(
            glossary_master=strdterm_master.glossary_master,
            term_name=strdterm_master.term_name,
            physical_term_name=strdterm_master.physical_term_name,
            rep_infotype=strdterm_master.rep_infotype,
            code_instances__0__exists=True,
        ).only('glossary_derived', 'code_instances')

        # too heavy work...
        code_instances = []
        for codeterm in codeterms:
            for instance in codeterm.virtual_code_instances:
                instance.inst_id = codeterm.glossary_derived.project.title
                code_instances.append(instance)
                current_app.logger.debug(instance)

        if sorted_ and code_instances:
            # None 은 비교가 안되므로 강제 문자열처리
            code_instances.sort(key=lambda x: str(getattr(x, sorted_)))
            if order == 'desc':
                code_instances.reverse()

        if search:
            code_instances = [
                c for c in code_instances
                if c.inst_value.find(search) >= 0 or
                c.inst_definition.find(search) >= 0 or
                c.inst_description.find(search) >= 0 or
                c.inst_remark.find(search) >= 0
            ]

        gen = (
            json.loads(obj.to_json())
            for obj in code_instances[offset:offset + limit]
        )
        headers = {
            'X-Total-Count': len(code_instances),
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            api_gen(gen, total=len(code_instances)),
            headers=headers,
            mimetype='application/json')


class ModelEntitiesResource(SingleListResource):

    input_cls = Model

    def get(self, id):
        '''queryset이 아니라 embeddedfieldlist이므로 직접구현'''

        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        sorted_ = request.args.get('sort', '')  # +field1,-field2
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text

        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()

        model = Model.objects.get_or_404(id=id)
        entities = model.entity_report(search)

        if sorted_ and entities:
            # None 은 비교가 안되므로 강제 문자열처리
            entities.sort(key=lambda x: str(x.get(sorted_, '')))
            if order == 'desc':
                entities.reverse()

        # if search:
        #     entities = [entity for entity in entities
        #                  if entity.entNm.find(search) >= 0 or
        #                  entity.tabNm.find(search) >= 0]

        gen = (
            obj
            for obj in entities[offset:offset + limit]
        )
        headers = {
            'X-Total-Count': len(entities),
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            api_gen(gen, total=len(entities)),
            headers=headers,
            mimetype='application/json')


class ModelCompleteCompareResource(SingleListResource):

    input_cls = Model

    def queryset(self, model_id):
        return ModelSchemaDiff.objects(model=ObjectId(model_id))


# /users
# /user/:id
# /user/:id/projects
# /user/:id/myprojects
# /user/:id/visitedprojects


# class UserListResource(SingleListResource):
#     resource_cls = User
#     input_cls = User
#     exclude_fields = ['password']


class UserResource(SingleResource):
    resource_cls = User
    input_cls = User
    exclude_fields = ['password']


def configure_api_btstptbl(app):
    def _(uri):
        return API_PREFIX + uri

    # api = Api(app)

    api = Blueprint('api_v1', __name__)

    # /projectgroups
    # /projectgroup/:slug
    # /projectgroup/:slug/users
    # /projectgroup/:slug/projects
    # /projectgroup/:slug/glossaries
    # /projectgroup/:slug/masterterms
    api.add_url_rule(
        _('/projectgroups'),
        view_func=ProjectGroupListResource.as_view(
            'ProjectGroupListResource'))
    api.add_url_rule(
        _('/projectgroup/<id>'),
        view_func=ProjectGroupResource.as_view(
            'ProjectGroupResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/users'),
        view_func=ProjectGroupUsersResource.as_view(
            'ProjectGroupUsersResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/projects'),
        view_func=ProjectGroupProjectsResource.as_view(
            'ProjectGroupProjectsResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/glossaries'),
        view_func=ProjectGroupGlossariesResource.as_view(
            'ProjectGroupGlossariesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/masterterms'),
        view_func=ProjectGroupMasterTermsResource.as_view(
            'ProjectGroupMasterTermsResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/entities'),
        view_func=ProjectGroupEntitiesResource.as_view(
            'ProjectGroupEntitiesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/tables'),
        view_func=ProjectGroupTablesResource.as_view(
            'ProjectGroupTablesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/attributes'),
        view_func=ProjectGroupAttributesResource.as_view(
            'ProjectGroupAttributesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/properties'),
        view_func=ProjectGroupPropertiesResource.as_view(
            'ProjectGroupPropertiesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/subjectareas'),
        view_func=ProjectGroupSubjectareasResource.as_view(
            'ProjectGroupSubjectareasResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/notices'),
        view_func=ProjectGroupNoticesResource.as_view(
            'ProjectGroupNoticesResource'))
    api.add_url_rule(
        _('/projectgroup/<id>/qna'),
        view_func=ProjectGroupQnAResource.as_view(
            'ProjectGroupQnAResource'))

    # /projects
    # /project/:id
    # /project/:id/users
    # /project/:id/glossaries
    # /project/:id/entities
    # /project/:id/attirbutes
    # /project/:id/tables
    # /project/:id/columns
    # /project/:id/erdlink
    api.add_url_rule(
        _('/projects'),
        view_func=ProjectListResource.as_view('ProjectListResource'))
    api.add_url_rule(
        _('/project/<mbj:id>'),
        view_func=ProjectResource.as_view('ProjectResource'))
    api.add_url_rule(
        _('/project/<mbj:id>/users'),
        view_func=ProjectUsersResource.as_view('ProjectUsersResource'))
    api.add_url_rule(
        _('/project/<mbj:id>/users/advsearch'),
        view_func=ProjectUsersAdvSearch.as_view('ProjectUsersAdvSearch'))
    api.add_url_rule(
        _('/project/<mbj:id>/glossaries'),
        view_func=ProjectGlossariesResource.as_view(
            'ProjectGlossariesResource'))
    api.add_url_rule(
        _('/project/<id>/entities'),
        view_func=ProjectEntitiesResource.as_view(
            'ProjectEntitiesResource'))
    api.add_url_rule(
        _('/project/<id>/tables'),
        view_func=ProjectTablesResource.as_view(
            'ProjectTablesResource'))
    api.add_url_rule(
        _('/project/<id>/attributes'),
        view_func=ProjectAttributesResource.as_view(
            'ProjectAttributesResource'))
    api.add_url_rule(
        _('/project/<id>/properties'),
        view_func=ProjectPropertiesResource.as_view(
            'ProjectPropertiesResource'))
    api.add_url_rule(
        _('/project/<mbj:id>/erdlink'),
        view_func=ProjectErdLinkResource.as_view(
            'ProjectErdLinkResource'))
    api.add_url_rule(
        _('/project/<mbj:id>/schemacollectors'),
        view_func=ProjectSchemaCollectorsResource.as_view(
            'ProjectSchemaCollectorsResource'))
    api.add_url_rule(
        _('/project/<mbj:id>/modelhistory'),
        view_func=ProjectModelHistoryResource.as_view(
            'ProjectModelHistoryResource'))

    # /schemacollector/<mbj:id>/resultlist
    # /schemacollector/<mbj:id>/schema
    api.add_url_rule(
        _('/schemacollector/<mbj:id>/resultlist'),
        view_func=SchemaCollectResultListResource.as_view(
            'SchemaCollectResultListResource'))
    api.add_url_rule(
        _('/schemacollector/<mbj:id>/schema'),
        view_func=SchemaCollectResultResource.as_view(
            'SchemaCollectResultResource'))

    api.add_url_rule(
        _('/user/<mbj:id>'),
        view_func=UserResource.as_view('UserResource'))
    # api.add_url_rule(
    #     _('/users'),
    #     view_func=UserListResource.as_view('UserListResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>'),
        view_func=GlossaryResource.as_view('GlossaryResource'))

    # /projectuser/:id
    # /projectuser/:id/roles
    api.add_url_rule(
        _('/projectuser/<mbj:id>'),
        view_func=ProjectUserResource.as_view('ProjectUserResource'))
    api.add_url_rule(
        _('/projectuser/<mbj:id>/glossaries'),
        view_func=ProjectUserGlossariesResource.as_view(
            'ProjectUserGlossariesResource'))
    api.add_url_rule(
        _('/projectuser/<mbj:id>/models'),
        view_func=ProjectUserModelsResource.as_view(
            'ProjectUserModelsResource'))

    # /glossaries
    # /glossary/:id
    # /glossary/:id/terms
    # /glossary/:id/terms/advsearch
    # /glossary/:id/strdterms
    # /glossary/:id/unitterms
    # /glossary/:id/codeterms
    # /glossary/:id/synonyms
    # /glossary/:id/domains
    # /glossary/:id/mydrafts
    # /glossary/:id/codesets
    # /glossary/:id/codeset/:csid
    # /glossary/:id/infotypes
    # /glossary/:id/reports
    api.add_url_rule(
        _('/glossary/<mbj:id>/terms'),
        view_func=GlossaryTermsResource.as_view('GlossaryTermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/terms/advsearch'),
        view_func=GlossaryTermsAdvSearch.as_view('GlossaryTermsAdvSearch'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/strdterms'),
        view_func=GlossaryStrdtermsResource.as_view(
            'GlossaryStrdtermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/unitterms'),
        view_func=GlossaryUnittermsResource.as_view(
            'GlossaryUnittermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/codeterms'),
        view_func=GlossaryCodetermsResource.as_view(
            'GlossaryCodetermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/draftterms'),
        view_func=GlossaryDrafttermsResource.as_view(
            'GlossaryDrafttermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/mydraftterms'),
        view_func=GlossaryMyDrafttermsResource.as_view(
            'GlossaryMyDrafttermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/normalcodeterms'),
        view_func=GlossaryNormalCodetermsResource.as_view(
            'GlossaryNormalCodetermsResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/infotypes'),
        view_func=GlossaryInfotyesResource.as_view('GlossaryInfotyesResource'))
    api.add_url_rule(
        _('/glossary/<mbj:id>/reports'),
        view_func=GlossaryReportsResource.as_view('GlossaryReportsResource'))

    # /glossarymaster/:id
    # /glossarymaster/:id/terms
    # /glossarymaster/:id/terms/advsearch
    # /glossarymaster/:id/strdterms
    # /glossarymaster/:id/unitterms
    # /glossarymaster/:id/codeterms
    # /glossarymaster/:id/synonyms
    # /glossarymaster/:id/domains
    # /glossarymaster/:id/mydrafts
    # /glossarymaster/:id/codesets
    # /glossarymaster/:id/codeset/:csid
    # /glossarymaster/:id/infotypes
    # /glossarymaster/:id/entities
    # /glossarymaster/:id/draftterms
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/strdterms'),
        view_func=GlossaryMasterStrdtermsResource.as_view(
            'GlossaryMasterStrdtermsResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/unitterms'),
        view_func=GlossaryMasterUnittermsResource.as_view(
            'GlossaryMasterUnittermsResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/infotypes'),
        view_func=GlossaryMasterInfotypesResource.as_view(
            'GlossaryMasterInfotypesResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/terms/advsearch'),
        view_func=GlossaryMasterTermsAdvSearchResource.as_view(
            'GlossaryMasterTermsAdvSearchResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/termrequests'),
        view_func=GlossaryMasterTermRequestsResource.as_view(
            'GlossaryMasterTermRequestsResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/termrequestsdone'),
        view_func=GlossaryMasterTermRequestsDoneResource.as_view(
            'GlossaryMasterTermRequestsDoneResource'))
    api.add_url_rule(
        _('/glossarymaster/<mbj:id>/codeterms'),
        view_func=GlossaryMasterCodeTermsResource.as_view(
            'GlossaryMasterCodeTermsResource'))
    # /glossaryderived/:id
    # /glossaryderived/:id/terms
    # /glossaryderived/:id/termrequests
    # /glossaryderived/:id/strdterms
    # /glossaryderived/:id/unitterms
    # /glossaryderived/:id/normalcodeterms
    # /glossaryderived/:id/codeterms
    # /glossaryderived/:id/synonyms
    # /glossaryderived/:id/domains
    # /glossaryderived/:id/mydrafts
    # /glossaryderived/:id/codesets
    # /glossaryderived/:id/codeset/:csid
    # /glossaryderived/:id/infotypes
    # /glossaryderived/:id/entities
    # /glossaryderived/:id/nonstrdterms
    # /glossaryderived/:id/draftterms
    # /glossaryderived/:id/reports

    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/terms/advsearch'),
        view_func=GlossaryDerivedTermsAdvSearchResource.as_view(
            'GlossaryDerivedTermsAdvSearchResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/termrequests'),
        view_func=GlossaryDerivedTermRequestsResource.as_view(
            'GlossaryDerivedTermRequestsResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/codeterms'),
        view_func=GlossaryDerivedCodeTermsResource.as_view(
            'GlossaryDerivedCodeTermsResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/nonstrdterms'),
        view_func=GlossaryDerivedNonStrdTermsResource.as_view(
            'GlossaryDerivedNonStrdTermsResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/nonstrdtermmaps'),
        view_func=GlossaryDerivedNonStrdTermMapsResource.as_view(
            'GlossaryDerivedNonStrdTermMapsResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/normalcodeterms'),
        view_func=GlossaryDerivedNormalCodeTermsResource.as_view(
            'GlossaryDerivedNormalCodeTermsResource'))
    api.add_url_rule(
        _('/glossaryderived/<mbj:id>/reports'),
        view_func=GlossaryDerivedReportsResource.as_view(
            'GlossaryDerivedReportsResource'))

    # /codeterm/:id/codeinstances
    api.add_url_rule(
        _('/codeterm/<mbj:id>/codeinstances'),
        view_func=CodeTermCodeInstancesResource.as_view(
            'CodeTermCodeInstancesResource'))

    # /term/:id
    # /term/:id/codeinstances
    # /term/:id/infotypes
    api.add_url_rule(
        _('/term/<mbj:id>/infotypes'),
        view_func=TermInfotypesResource.as_view('TermInfotypesResource'))
    api.add_url_rule(
        _('/term/<mbj:id>/codeinstances'),
        view_func=TermCodeInstancesResource.as_view(
            'TermCodeInstancesResource'))

    # /termmaster/:id
    # /termmaster/:id/codeinstances
    # /termmaster/:id/projectcodeinstances
    # /termmaster/:id/infotypes
    api.add_url_rule(
        _('/termmaster/<mbj:id>/infotypes'),
        view_func=TermMasterInfotypesResource.as_view(
            'TermMasterInfotypesResource'))
    api.add_url_rule(
        _('/termmaster/<mbj:id>/projectcodeinstances'),
        view_func=TermMasterProjectCodeInstancesResource.as_view(
            'TermMasterProjectCodeInstancesResource'))

    # /model/:id/entities
    # /model/:id/completecompare
    api.add_url_rule(
        _('/model/<mbj:id>/entities'),
        view_func=ModelEntitiesResource.as_view('ModelEntitiesResource'))
    api.add_url_rule(
        _('/model/<mbj:id>/completecompare'),
        view_func=ModelCompleteCompareResource.as_view('ModelCompleteCompareResource'))

    app.register_blueprint(api)
