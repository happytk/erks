from itertools import islice
from bson import ObjectId
from flask import jsonify
from flask import Blueprint, request, current_app, stream_with_context
from flask.views import MethodView as Resource
from ercc.ercc_bps.erc.models import ProjectERD
from ercc.models import (
    GlossaryBase,
    GlossaryDerived,
    # GlossaryMaster,
    Model,
    Entity,
    Project,
    ProjectGroup,
    ProjectSummary,
    # StrdTermMaster,
    SubjectArea,
)
from ercc.ercc_bps.api.v1 import (
    SingleListResource,
    SingleGenResource,
    # SingleResource,
    api_gen,
)
from ercc.ercc_bps.api.v1.btstptbl import (
    ProjectGroupSubjectareasResource,
)
import json

API_PREFIX = '/api_skb'


# api(skb) specification

# spec#1 - /projectgroup/<id>/termmasters
# spec#2 - /projectgroup/<id>/subjectareas
# spec#3 - /projectgroup/<id>/projects_yesterday
# spec#4 - /projectgroup/<id>/strdattrs?search=<논리명>
# spec#5 - /projectgroup/<id>/summary
# spec#7 - /projectgroup/<id>/attributes
# spec#8 - /projectgroup/<id>/modelreports
# spec#9 - /projectgroup/<id>/projectgroupuser <post>
# spec#10- /projectgroup/<id>/attrpump


class ProjectGroupModelReportsResource(SingleListResource):
    input_cls = ProjectGroup

    def get(self, id):

        limit = request.args.get('limit', 10, int)
        offset = request.args.get('offset', 0, int)
        sorted_ = request.args.get('sort', '')  # +field1,-field2

        # queryset
        project_group = ProjectGroup.objects.get(slug=id)
        query = project_group.queryset_project

        # total_count
        total_count = query.count()

        def _get_glossary_matched_rate(project):
            report = project.queryset_model_report.order_by('-created_at').only('matched_rate').first()
            if report:
                return report.matched_rate
            else:
                return 0

        gen = (
            {
                'project_id': str(project.id),
                'project_title': project.title,
                'glossary_matched_rate': _get_glossary_matched_rate(project),
                'physical_matched_rate': project.physical_model_matched_rate,
            }
            for project in query.order_by(sorted_).skip(offset).limit(limit)
        )

        headers = {
            'X-Total-Count': total_count,
        }
        headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            stream_with_context(api_gen(gen, total=total_count)),
            headers=headers,
            mimetype='application/json')


class ProjectGroupTermMastersResource(SingleListResource):
    '''전사용어사전의 표준용어 목록'''

    exclude_fields = [
        'composition',
        'composition_verified',
        'created_by',
        'domain',
        'glossary_master',
        'id',
        'infotypes',
        'is_domain',
        'is_domain_inheritable',
        'modified_by',
        'project_group',
        'rep_infotype',
        'rep_unitterm',
    ]
    input_cls = ProjectGroup

    def queryset(self, id):
        glossary = ProjectGroup.objects.get_or_404(slug=id).glossary_master
        return glossary.queryset_term

    def search(self, query, search_string):
        from mongoengine import Q
        return query.filter(
            Q(term_name__icontains=search_string) |
            Q(physical_term_name__icontains=search_string)
        )

    def get(self, *args, **kwargs):
        '''
        전사용어사전의 용어 목록(표준용어, 표준단어, 금칙어)
        ---
        tags:
          - glossarymaster
        definitions:
          - schema:
              id: attribute
              properties:
                title:
                 type: string
                 description: 프로젝트이름
                description:
                 type: string
                 description: 프로젝트요약
                id:
                 type: string
                 description: 프로젝트id
                url:
                 type: string
                 description: 프로젝트접속url
        parameters:
          - in: path
            name: id
            required: true
            description: glossary의 고유id
        responses:
          200:
            description: 관리프로젝트에 대한 요약정보 노출
            schema:
              type: array
              description: list of groups
              items:
                $ref: '#/definitions/attribute'
        '''
        return super().get(*args, **kwargs)


class ProjectGroupSummaryResource(Resource):
    def get(self, id):
        '''
        관리프로젝트에 대한 요약
        ---
        tags:
          - projectgroup
          - skb
        definitions:
          - schema:
              id: ProjectSummary
              properties:
                title:
                 type: string
                 description: 프로젝트이름
                description:
                 type: string
                 description: 프로젝트요약
                id:
                 type: string
                 description: 프로젝트id
                url:
                 type: string
                 description: 프로젝트접속url
        parameters:
          - in: path
            name: id
            required: true
            example: skbmeta
            description: project_group_slug
        responses:
          200:
            description: 관리프로젝트에 대한 요약정보 노출
            schema:
              type: array
              description: list of groups
              items:
                $ref: '#/definitions/ProjectSummary'
        '''
        project_group = ProjectGroup.objects.get_or_404(slug=id)
        projects = list(project_group.queryset_project(
            project_group_managed=True).only(
                'id', 'title', 'description', 'project_group', 'profile_imgf'))

        def project_to_dict(p):
            d = dict(
                title=p.title,
                description=p.description,
                url=p.url,
                img_url=p.get_profile_img_url(),
            )
            d.update(ProjectSummary.get_erc_info(p))
            return d

        return jsonify(
            total=len(projects),
            rows=[
                project_to_dict(project)
                for project in projects
            ]
        )

class ProjectGroupEntityHistoryResource(Resource):
    input_cls = ProjectGroup

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

        project_group = ProjectGroup.objects.get_or_404(slug=id)
        projects = list(project_group.queryset_project(project_group_managed=True))

        from .btstptbl import ProjectModelHistoryResource

        def get_project_history(project_id):
            # from datetime import datetime, timedelta
            # yesterday = (datetime.today()-timedelta(1)).strftime("%Y%m%d")
            project_history_resource = ProjectModelHistoryResource()
            projects_history_list = project_history_resource.get_history_list(project_id=project_id,
                                                                              date_from=date_from, date_to=date_to)

            def get_entity_mod_count(history_dtl):
                return len([x for x in history_dtl if x["object_type"] == "entity"])

            project_history_dtl = [
                {
                    "project_id": str(project["id"]),
                    "ent_mods": get_entity_mod_count(project["dtl"])
                }
                for project in projects_history_list
            ]

            dtl_count = sum(x["ent_mods"] for x in project_history_dtl)
            return dtl_count

        def get_project_entity_mod_dtl(project_id):
            # from datetime import datetime, timedelta
            # yesterday = (datetime.today()-timedelta(1)).strftime("%Y%m%d")
            project_history_resource = ProjectModelHistoryResource()
            projects_history_list = project_history_resource.get_history_list(project_id=project_id,
                                                                              date_from=date_from, date_to=date_to)

            entity_mod_map = {}

            prj_erd = ProjectERD(project_id)
            for project_history in projects_history_list:
                for dtl in project_history["dtl"]:
                    if "object_type" in dtl and dtl["object_type"] == "entity":
                        if "logical_name" in dtl:
                            entity_mod_map[dtl["logical_name"]] = {
                                "logical_name": dtl["logical_name"],
                                "physical_name": dtl["physical_name"],
                                "url": prj_erd.url(entNm=dtl["logical_name"]),
                            }

            project_entity_mod_dtl = {
                "modified_entities": [v for k, v in entity_mod_map.items()],
                "unique_modified_entities_count": len(entity_mod_map.items()),
                "source_data": projects_history_list
            }

            return project_entity_mod_dtl

        project_summary = [
            {
                "id": str(project["id"]),
                "title": project["title"],
                "desc": project["description"],
                "contact": project["contact"],
                "entity_mod_count": get_project_history(str(project["id"])),
                "entity_mod_dtl": get_project_entity_mod_dtl(str(project["id"])),
                "url": project.url,
            }
            for project in projects
        ]

        return jsonify(project_summary)

class ProjectGroupAttributesResource(SingleGenResource):
    input_cls = ProjectGroup

    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '-')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)
        prj_ids = [
            str(p.id)
            for p in Project.objects(project_group=pg, private=False).only('id')
        ]

        def _patch(d, entity):
            '''d에 entity정보를 patch'''
            d['prjId'] = getattr(entity, 'prjId', '0' * 24)
            prj = Project.objects(id=ObjectId(d['prjId'])).first()
            d['prjNm'] = prj.title if prj else ''
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            model = Model.objects(
                entities=str(entity.id),
                newest='Y'
            ).first()
            d['modelNm'] = model.name if model else ''
            d['modelOid'] = str(model.Oid) if model else ''
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(attr.get('Lattr', {}), entity),
                    ensure_ascii=False,
                    indent=(not request.is_xhr),
                    sort_keys=(not request.is_xhr),
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

    def get(self, *args, **kwargs):
        '''
        모든 속성(attributes)정보
        ---
        tags:
          - projectgroup
          - skb
        definitions:
          - schema:
              id: attribute
              properties:
                title:
                 type: string
                 description: 프로젝트이름
                description:
                 type: string
                 description: 프로젝트요약
                id:
                 type: string
                 description: 프로젝트id
                url:
                 type: string
                 description: 프로젝트접속url
        parameters:
          - in: path
            name: id
            required: true
            example: skbmeta
            description: project_group_slug
        responses:
          200:
            description: 관리프로젝트에 대한 요약정보 노출
            schema:
              type: array
              description: list of groups
              items:
                $ref: '#/definitions/attribute'
        '''
        return super().get(*args, **kwargs)


class ProjectGroupStrdAttributesResource(SingleGenResource):
    '''project-group에 속한 모든 표준속성명을 검색한다.
    projectgroup내 project를 검색,
    project내 model을 검색,
    model내 entity를 검색,
    entity내 attributes를 검색,
    attributes가 검색용어에 정확하게 일치하는지를 검사.
    attributes가 표준용어사전에 속한 것인지를 검사'''

    input_cls = ProjectGroup

    def gen(self, **kwargs):
        offset = kwargs.get('offset')
        limit = kwargs.get('limit')
        search = kwargs.get('search', '-')
        id = kwargs.get('id')

        pg = ProjectGroup.objects.get_or_404(slug=id)

        def gen():
            first_gen = (
                (
                    project,
                    model,
                    GlossaryBase.head_objects(id=model.glossaryId).first(),
                    # Entity.objects(
                    #     prjId=str(project.id), id=ObjectId(entity_id),
                    #     newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
                )
                for project in Project.objects(project_group=pg, private=False).only('id', 'title')
                for model in Model.objects(prjId=str(project.id), newest='Y')
                if hasattr(model, 'glossaryId') and model.glossaryId and hasattr(model, 'dbmsType') and model.dbmsType
            )
            # first_gen = list(first_gen)
            # current_app.logger.debug(f'first_gen: {len(first_gen)}')
            # second_gen = (
            #     (
            #         project,
            #         model,
            #         glossary,
            #         Entity.objects(
            #             prjId=str(project.id), id=ObjectId(entity_id),
            #             newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
            #     )
            #     for project, model, glossary in first_gen
            #     if glossary is not None
            #     for entity_id in model.entities
            # )

            second_gen = (
                (
                    project,
                    model,
                    glossary,
                    SubjectArea.objects(prjId=str(project.id), id=str(subjectarea_ids.get('id'))).only('name', 'Oid', 'entities').first()
                )
                for project, model, glossary in first_gen
                if glossary is not None
                for subjectarea_ids in model.subjectareas
            )
            # second_gen = list(second_gen)
            # current_app.logger.debug(f'second_gen: {len(second_gen)}')

            third_gen = (
                (
                    project,
                    model,
                    glossary,
                    subjectarea,
                    Entity.objects(
                        prjId=str(project.id), id=ObjectId(entity_obj.get('id')),
                        newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
                )
                for project, model, glossary, subjectarea in second_gen
                if subjectarea is not None
                for entity_obj in subjectarea.entities
            )
            # third_gen = list(third_gen)
            # current_app.logger.debug(f'third_gen: {len(third_gen)}')

            last_gen = (
                (
                    project,
                    model,
                    glossary,
                    subjectarea,
                    entity,
                    attr,
                    ProjectERD(project.id).url(subjId=subjectarea.id, entNm=entity.entNm, attrNm=attr.get('Lattr', {}).get('attrNm', ''))
                )
                for project, model, glossary, subjectarea, entity in third_gen
                if entity is not None
                for attr in entity.attrs
                if search in attr.get('Lattr', {}).get('attrNm', '')
                if glossary.is_strdterm(
                    attr.get('Lattr', {}).get('attrNm', ''),
                    attr.get('Pattr', {}).get('colNm', ''),
                    attr.get('Lattr', {}).get('dataTyp', ''),
                    attr.get('Pattr', {}).get('dataTyp', ''),
                    model.dbmsType
                )
            )
            return last_gen

        def _patch(project, model, glossary, subjectarea, entity, attr, url):
            '''최종적으로 전송할 데이터 정리'''
            attr = dict(attr.get('Lattr', {}))
            d = {}
            d['attrNm'] = attr.get('attrNm', '')
            d['attrDef'] = attr.get('attrDef', '')
            d['prjId'] = str(project.id)
            d['prjNm'] = project.title
            d['modelNm'] = model.name if model else ''
            d['modelOid'] = str(model.Oid) if model else ''
            d['subjectAreaNm'] = subjectarea.name
            d['subjectAreaOid'] = str(subjectarea.Oid)
            d['entNm'] = getattr(entity, 'entNm', '')
            d['tabNm'] = getattr(entity, 'tabNm', '')
            d['url'] = url
            return d

        yield from islice(
            (
                json.dumps(
                    _patch(*args),
                    ensure_ascii=False,
                    indent=(not request.is_xhr),
                    sort_keys=(not request.is_xhr),
                )
                for args in gen()
            ),
            offset,
            limit,
        )

    def get(self, *args, **kwargs):
        '''
        모든 속성중 '표준용어'로 등록된 대상에 한정하여 검색
        ---
        tags:
          - projectgroup
          - skb
        definitions:
          - schema:
              id: ProjectSummary
              properties:
                title:
                 type: string
                 description: 프로젝트이름
                description:
                 type: string
                 description: 프로젝트요약
                id:
                 type: string
                 description: 프로젝트id
                url:
                 type: string
                 description: 프로젝트접속url
        parameters:
          - in: path
            name: id
            required: true
            example: skbmeta
            description: project_group_slug
          - id: query
            name: search
            required: true
            description: 검색하고자 하는 논리속성명
        responses:
          200:
            description: 관리프로젝트에 대한 요약정보 노출
            schema:
              type: array
              description: list of groups
              items:
                $ref: '#/definitions/ProjectSummary'
        '''
        return super().get(*args, **kwargs)


class ProjectGroupAttrPumpResource(Resource):
    '''project-group에 속한 모든 표준속성명을 검색한다.

    projectgroup내 project를 검색,
    project내 model을 검색,
    model내 entity를 검색,
    entity내 attributes를 검색,
    attributes가 검색용어에 정확하게 일치하는지를 검사.
    attributes가 표준용어사전에 속한 것인지를 검사'''

    input_cls = ProjectGroup

    def get(self, id):
        pg = ProjectGroup.objects.get_or_404(slug=id)

        def gen():
            first_gen = (
                (
                    project,
                    model,
                    GlossaryDerived.head_objects(id=model.glossaryId).first(),
                    # Entity.objects(
                    #     prjId=str(project.id), id=ObjectId(entity_id),
                    #     newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
                )
                for project in Project.objects(project_group=pg, private=False).only('id', 'title')
                for model in Model.objects(prjId=str(project.id), newest='Y')
                if hasattr(model, 'glossaryId') and model.glossaryId and hasattr(model, 'dbmsType') and model.dbmsType
            )
            first_gen = list(first_gen)
            current_app.logger.debug(f'first_gen: {len(first_gen)}')
            # second_gen = (
            #     (
            #         project,
            #         model,
            #         glossary,
            #         Entity.objects(
            #             prjId=str(project.id), id=ObjectId(entity_id),
            #             newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
            #     )
            #     for project, model, glossary in first_gen
            #     if glossary is not None
            #     for entity_id in model.entities
            # )

            second_gen = (
                (
                    project,
                    model,
                    glossary,
                    SubjectArea.objects(prjId=str(project.id), id=str(subjectarea_ids.get('id'))).only('name', 'Oid', 'entities').first()
                )
                for project, model, glossary in first_gen
                if glossary is not None
                for subjectarea_ids in model.subjectareas
            )
            second_gen = list(second_gen)
            current_app.logger.debug(f'second_gen: {len(second_gen)}')

            third_gen = (
                (
                    project,
                    model,
                    glossary,
                    subjectarea,
                    Entity.objects(
                        prjId=str(project.id), id=ObjectId(entity_obj.get('id')),
                        newest='Y', entTyp__ne='P', attrs__0__exists=True).first(),
                )
                for project, model, glossary, subjectarea in second_gen
                if subjectarea is not None
                for entity_obj in subjectarea.entities
            )
            third_gen = list(third_gen)
            current_app.logger.debug(f'third_gen: {len(third_gen)}')

            last_gen = (
                (
                    project,
                    model,
                    glossary,
                    subjectarea,
                    entity,
                    attr,
                    glossary.infer_strdtermname(
                        attr.get('Lattr', {}).get('attrNm', ''),
                        attr.get('Pattr', {}).get('colNm', ''),
                        attr.get('Lattr', {}).get('dataTyp', ''),
                        attr.get('Pattr', {}).get('dataTyp', ''),
                        model.dbmsType
                    ),
                    glossary.is_strdterm(
                        attr.get('Lattr', {}).get('attrNm', ''),
                        attr.get('Pattr', {}).get('colNm', ''),
                        attr.get('Lattr', {}).get('dataTyp', ''),
                        attr.get('Pattr', {}).get('dataTyp', ''),
                        model.dbmsType
                    ),
                    glossary.is_strdtermmap(
                        attr.get('Lattr', {}).get('attrNm', ''),
                        attr.get('Pattr', {}).get('colNm', ''),
                        attr.get('Lattr', {}).get('dataTyp', ''),
                        attr.get('Pattr', {}).get('dataTyp', ''),
                        model.dbmsType
                    ),
                    ProjectERD(project.id).url(subjId=subjectarea.id, entNm=entity.entNm),
                    ProjectERD(project.id).url(subjId=subjectarea.id, entNm=entity.entNm, attrNm=attr.get('Lattr', {}).get('attrNm', ''))
                )
                for project, model, glossary, subjectarea, entity in third_gen
                if entity is not None
                for attr in entity.attrs
            )
            return last_gen

        def _patch(project, model, glossary, subjectarea, entity, attr, termname, is_strdterm, is_strdtermmap, entity_url, attr_url):
            '''최종적으로 전송할 데이터 정리'''
            attr = dict(attr.get('Lattr', {}))
            d = {}
            d['attrDef'] = attr.get('attrDef', '')
            d['attrNm'] = attr.get('attrNm', '')
            d['attrUrl'] = attr_url
            d['entNm'] = getattr(entity, 'entNm', '')
            d['entUrl'] = entity_url
            d['entOid'] = str(entity.Oid)
            d['isStrdTerm'] = is_strdterm
            d['isStrdTermMap'] = is_strdtermmap
            d['modelNm'] = model.name if model else ''
            d['modelOid'] = str(model.Oid) if model else ''
            d['prjId'] = str(project.id)
            d['prjNm'] = project.title
            d['strdTermName'] = termname
            d['subjectAreaNm'] = subjectarea.name
            d['subjectAreaOid'] = str(subjectarea.Oid)
            d['tabNm'] = getattr(entity, 'tabNm', '')
            return d

        headers = {
            # 'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        # headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            stream_with_context(api_gen(
                json.dumps(
                    _patch(*args),
                    ensure_ascii=False,
                    indent=(not request.is_xhr),
                    sort_keys=(not request.is_xhr),
                )
                for args in gen()
            )),
            headers=headers,
            mimetype='application/json')
        # return current_app.response_class(
        #     stream_with_context(api_gen(gen())),
        #     headers=headers,
        #     mimetype='application/json')


# spec#1 - /projectgroup/<id>/termmasters
# spec#2 - /projectgroup/<id>/subjectareas
# spec#3 - /projectgroup/<id>/projects_yesterday
# spec#4 - /projectgroup/<id>/strdattrs?search=<논리명>
# spec#5 - /projectgroup/<id>/summary
# spec#7 - /projectgroup/<id>/attributes
# spec#8 - /projectgroup/<id>/modelreports
# spec#9 - /projectgroup/<id>/projectgroupuser <post>
# spec#10- /projectgroup/<id>/attrpump

def configure_api_skb(app):
    def _build_url(uri):
        return API_PREFIX + uri

    api = Blueprint('api_skb', __name__)
    api.add_url_rule(_build_url('/projectgroup/<id>/termmasters'), view_func=ProjectGroupTermMastersResource.as_view('ProjectGroupTermMastersResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/subjectareas'), view_func=ProjectGroupSubjectareasResource.as_view('ProjectGroupSubjectareasResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/projects_entity_history'), view_func=ProjectGroupEntityHistoryResource.as_view('ProjectGroupEntityHistoryResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/strdattrs'), view_func=ProjectGroupStrdAttributesResource.as_view('ProjectGroupStrdAttributesResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/summary'), view_func=ProjectGroupSummaryResource.as_view('ProjectGroupSummaryResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/attributes'), view_func=ProjectGroupAttributesResource.as_view('ProjectGroupAttributesResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/modelreports'), view_func=ProjectGroupModelReportsResource.as_view('ProjectGroupModelReportsResource'))
    api.add_url_rule(_build_url('/projectgroup/<id>/attrpump'), view_func=ProjectGroupAttrPumpResource.as_view('ProjectGroupAttrPumpResource'))
    # api.add_url_rule(_build_url('/projectgroup/<id>/projectgroupuser'), view_func=ProjectGroupAttributesResource.as_view('ProjectGroupAttributesResource'))

    app.register_blueprint(api)
