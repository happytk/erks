# -*-encoding:utf-8-*-
"""
Flaskapp-views에 대한 사용자권한관리.

- 하나의 VIEW에 대해서 한개의 ROLE만 지정가능합니다.
- ROLE은 기본적으로 다음으로 분류합니다.

-- 프로젝트 관리자
-- 프로젝트 모델러/용어관리자
-- 프로젝트 사용자
-- 프로젝트그룹 사용자
-- 로그인한 사용자
-- 로그인하지않은 사용자

특징
- 상위ROLE은 하위ROLE을 포함합니다. 즉 로그인하지 않은 사용자의 VIEW는 로그인한 사용자가 볼 수 있습니다.
- 아무것도 지정하지 않을 경우의 기본값은 '로그인하지않은 사용자'입니다.
- 프로젝트 사용자는 프로젝트 권한에 따라 허가/불가가 동적으로 결정
- 프로젝트 그룹사용자는 프로젝트 그룹 권한에 따라 허가/불가가 동적으로 결정

"""

import logging
from flask_login import current_user
from flask_babel import gettext
from flask import g, request, abort, current_app, redirect, url_for
from erks.models import ProjectUser, ProjectGroupUser
from erks.utils import flash_error
from mongoengine import Q

CHECK_PROJECT_MEMBER = 'check_project_member'
CHECK_PROJECT_OWNER = 'check_project_owner'
CHECK_PROJECT_MODELER = 'check_project_modeler'
CHECK_PROJECT_TERMMGR = 'check_project_termmgr'
CHECK_LOGIN = 'login_required'
CHECK_NOTHING = ''


class SkipCheckPermissionError(Exception):
    pass


class CheckPermissionError(Exception):
    def __init__(self, response, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response = response


def _build_context():
    from erks.models import (
        # GlossaryDerived,
        # GlossaryMaster,
        # TermMaster,
        ProjectUserBase,
        # CodeTerm,
        # TermMasterRequest,
        # InfoTypeMaster,
        # CodeTermMaster,
        Post,
        Project,
        ProjectGroup,
        # InfoType,
        # Glossary,
        # Term,
        # NonStrdTermMap,
    )
    # import pdb; pdb.set_trace()
    check_args = {
        # 'codeterm_id': CodeTerm,
        # 'codeterm_master_id': CodeTermMaster,
        # 'glossary_derived_id': GlossaryDerived,  # -> glossary_derived_id
        # 'glossary_id': Glossary,
        # 'glossary_master_id': GlossaryMaster,  # glossary_master_id
        # 'infotype_id': InfoType,
        # 'infotype_master_id': InfoTypeMaster,
        'post_id': Post,
        'project_id': Project,
        'project_user_id': ProjectUserBase,
        'slug': ProjectGroup,
        # 'term_id': Term,
        # 'term_master_id': TermMaster,
        # 'term_master_request_id': TermMasterRequest,
        # 'nonstrdtermmap_id': NonStrdTermMap,
    }

    # 모든 g는 초기화하고 사용하기
    # g는 사실 request마다 새롭게 사용하는 것으로 생각하지만,
    # localproxy는 엄밀히 말하면 request-bound가 아니기 때문에
    # test-case에서 같은 test function내 request가 여러번 발생하면
    # g내 속성이 남아있는다.

    for arg in check_args.keys():
        if arg.endswith('_id'):
            setattr(g, arg[:-3], None)
    g.project_group = None

    view_args = request.view_args
    for arg in check_args.keys():
        if arg in view_args:
            found_value = view_args.get(arg)
            found_args = arg
            break
    else:
        found_args = None
        found_value = None

    if found_args:
        if found_args == 'slug':  # hack!
            obj = ProjectGroup.objects.get_or_404(slug=found_value)
            g.project_group = obj
        else:
            # if found_args == 'term_id':
            #     abort(404)
            obj = check_args[found_args].objects.get_or_404(id=found_value)
            current_app.logger.debug(f'[g-setter] {found_args[:-3]} {obj}')
            setattr(g, found_args[:-3], obj)
    elif 'id' in view_args and request.endpoint.startswith('api_'):
        from erks.erks_bps.api.v1 import skb, btstptbl, select2

        def _get_api_cls(endpoint, attrname):
            mod, cls_ = endpoint.split('.')
            if mod == 'api_skb':
                return getattr(getattr(skb, cls_), attrname, None)
            elif mod == 'api_v1':
                return getattr(getattr(btstptbl, cls_), attrname, None)
            elif mod == 'api_select2':
                return getattr(getattr(select2, cls_), attrname, None)
            else:
                current_app.logger.critical(f'{mod} is not considered.')

        def _func_sig(endpoint):
            return _get_api_cls(endpoint, 'input_cls')

        cls_ = _func_sig(request.endpoint)
        if cls_ is not None:
            if cls_ == ProjectGroup:
                obj = cls_.objects.get_or_404(slug=view_args.get('id'))
            else:
                obj = cls_.objects.get_or_404(id=view_args.get('id'))
            for k, v in check_args.items():
                if v == cls_:
                    setattr(g, k[:-3], obj)
                    break
        else:
            obj = None
    else:
        obj = None

    if obj:
        wanted = [
            # 'glossary_derived',
            'project',
            'project_group',
            # 'glossary_master',
            # 'glossary'
        ]
        for field in wanted:
            if hasattr(obj, field):
                setattr(g, field, getattr(obj, field))
        # if g.glossary and not g.project:
        #     g.project = g.glossary.project
        # if g.glossary_derived and not g.project:
        #     g.project = g.glossary_derived.project
        if g.project and not g.project_group:
            g.project_group = g.project.project_group
        # if g.glossary_master and not g.project_group:
        #     g.project_group = g.glossary_master.project_group


def _check_permission_demo():
    if not g.project:
        return
    project = g.project
    if project.demo:
        if request.endpoint in (
                'erc.ercapp',
                'erc.get_ercapp_erd',
                'erc.get_subj_tree'):
            raise SkipCheckPermissionError()
        else:
            raise CheckPermissionError(
                response=redirect(url_for('erc.ercapp', project_id=project.id)))


def _check_permission_login():
    # do_nothing이 아니면 기본적으로 login체크하기
    check_what = VIEWS_PERMISSION.get(request.endpoint, CHECK_NOTHING)
    if check_what == CHECK_NOTHING:
        return

    if current_user and current_user.is_active:
        return

    if request.is_xhr:
        abort(401)
    else:
        raise CheckPermissionError(response=redirect(url_for('login.login')))


def _check_permission_project_group():
    if not g.project_group:
        return
    pg = g.project_group
    if pg.is_default or pg.slug == current_app.config['DEFAULT_PROJECT_GROUP_SLUG']:
        return
    if request.endpoint.startswith('api'):  # TODO skb_api 권한 오류로 임시 변경
        return
    if pg.use_firewall:
        if request.headers.getlist("X-Forwarded-For"):
            ipaddr = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ipaddr = request.remote_addr
        if not pg.check_allowed_ip(ipaddr):
            logging.debug(
                f"IP {ipaddr} Cannot reach this page {request.endpoint}")
            abort(403)

    grade = pg.get_grade(current_user._get_current_object())
    if grade not in ['owner', 'manager', 'member', 'termer']:
        logging.debug(
            f"[pg_member_check][{grade}]"
            f" blocked the access to the view function"
            f"({request.endpoint})")
        abort(403)
    if (current_app.config['BILLING'] and
            grade != 'owner' and
            pg.is_expired):
        logging.debug(
            f"[pg_member_check]"
            f" blocked the access to expired group"
            f"({request.endpoint})")
        abort(403)  # 402


def _check_permission_project():
    if not g.project:
        return
    check_what = VIEWS_PERMISSION.get(request.endpoint, CHECK_NOTHING)
    if check_what == CHECK_NOTHING:
        return
    project = g.project

    # if current_app.config['BILLING'] and project.is_expired:
    #     grades = project._get_grades(current_user._get_current_object())
    #     if project.ORGANIZER not in grades:
    #         if request.is_xhr:
    #             abort(403)  # 402
    #         else:
    #             flash_error(gettext(u'이 프로젝트는 더 이상 사용하실 수 없습니다.'))
    #             raise CheckPermissionError(
    #                 response=redirect('portal.index'))

    if check_what == CHECK_PROJECT_OWNER:
        grades = project._get_grades(current_user._get_current_object())
        if project.ORGANIZER in grades:
            return
    elif check_what == CHECK_PROJECT_MODELER:
        grades = project._get_grades(current_user._get_current_object())
        if project.MODELER in grades or project.ORGANIZER in grades:
            return
    elif check_what == CHECK_PROJECT_TERMMGR:
        if g.glossary:
            user = current_user._get_current_object()
            if user in g.glossary.context_termers:
                return
        else:
            grades = project._get_grades(current_user._get_current_object())
            if project.TERM_MANAGER in grades or project.ORGANIZER in grades:
                return
    elif check_what in (CHECK_PROJECT_MEMBER, CHECK_LOGIN):
        user = current_user._get_current_object()
        if project.check_to_enter(user):
            return

    if request.is_xhr:
        abort(403)  # https://ko.wikipedia.org/wiki/HTTP_상태_코드
    else:
        raise CheckPermissionError(
            response=redirect(url_for(
                'project.not_seen', project_id=project.id)))
        # raise CheckPermissionError(
        #     response=render_template('project/not_seen.html', project=project))


"""
이 dict에 저장된 views는 config['BILLING']이 false일 경우 404처리됩니다.
"""
VIEWS_FOR_BILLING = [
    'portal.services',
    'portal._project_billing_ksnet_rcv',
    'project.create_project_plus',
    'project.create_project_plus_result',
    'project.cancel_subscription',
    'project.subscription',
    'project._subscription_log',
    'project._subscription_ksnet_result',
    'project_group.pg_create_ksnet',
    'project_group.pg_create_ksnet_result',
    'project_group.pg_cancel_subscription',
    'project_group.pg_subscription',
    'project_group._pg_subscription_log',
    'project_group._pg_subscription_ksnet_result',
]


"""
permission은 여기서 통합관리합니다.
"""
VIEWS_PERMISSION = {
    # 'erc.get_entity_subj_list': 'check_project_member',
    # 'erc.get_Sja_Ent_Rel': 'check_project_member',
    # 'erc.get_subj_tree': 'check_project_member',
    # 'erks_components.static': '',
    # 'erks_components.template_index': '',
    # 'glossary._glossary_draft_terms': CHECK_PROJECT_MEMBER,
    # 'glossary._glossary_recent_infotypes': CHECK_PROJECT_MEMBER,
    # 'glossary._glossary_recent_terms': CHECK_PROJECT_MEMBER,
    # 'portal.download_file': '',
    'admin.index': '',
    'admin.static':'',
    'analytics.index':'',
    'api_select2.GlossaryDomainsResource':'',
    'api_skb.ProjectGroupAttributesResource':'',
    'api_skb.ProjectGroupAttrPumpResource':'',
    'api_skb.ProjectGroupModelReportsResource':'',
    'api_skb.ProjectGroupStrdAttributesResource':'',
    'api_skb.ProjectGroupSubjectareasResource':'',
    'api_skb.ProjectGroupSummaryResource':'',
    'api_skb.ProjectGroupTermMastersResource':'',
    # 'api_skb.ProjectGroupYesterdayHistoryResource':'',
    'api_skb.ProjectGroupEntityHistoryResource':'',
    'api_v0._strd_term_codelist': '',
    'api_v0._strd_term_list': '',
    'api_v1.CodeTermCodeInstancesResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryCodetermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedCodeTermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedNonStrdTermMapsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedNonStrdTermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedNormalCodeTermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedReportsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedTermRequestsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDerivedTermsAdvSearchResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryDrafttermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryInfotyesResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryMasterCodeTermsResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterInfotypesResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterStrdtermsResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterTermRequestsDoneResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterTermRequestsResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterTermsAdvSearchResource': CHECK_LOGIN,
    'api_v1.GlossaryMasterUnittermsResource': CHECK_LOGIN,
    'api_v1.GlossaryMyDrafttermsResource': CHECK_LOGIN,
    'api_v1.GlossaryNormalCodetermsResource': CHECK_LOGIN,
    'api_v1.GlossaryReportsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryStrdtermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryTermsAdvSearch': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryTermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.GlossaryUnittermsResource': CHECK_PROJECT_MEMBER,
    'api_v1.ModelCompleteCompareResource':'',
    'api_v1.ModelEntitiesResource':'',
    'api_v1.ProjectAttributesResource':'',
    'api_v1.ProjectEntitiesResource':'',
    'api_v1.ProjectErdLinkResource':'',
    'api_v1.ProjectGlossariesResource':'',
    'api_v1.ProjectGroupAttributesResource':'',
    'api_v1.ProjectGroupEntitiesResource':'',
    'api_v1.ProjectGroupGlossariesResource':'',
    'api_v1.ProjectGroupListResource':'',
    'api_v1.ProjectGroupMasterTermsResource':'',
    'api_v1.ProjectGroupNoticesResource':'',
    'api_v1.ProjectGroupProjectsResource':'',
    'api_v1.ProjectGroupPropertiesResource':'',
    'api_v1.ProjectGroupQnAResource':'',
    'api_v1.ProjectGroupResource':'',
    'api_v1.ProjectGroupSubjectareasResource':'',
    'api_v1.ProjectGroupTablesResource':'',
    'api_v1.ProjectGroupUsersResource':'',
    'api_v1.ProjectListResource':'',
    'api_v1.ProjectModelHistoryResource':'',
    'api_v1.ProjectPropertiesResource':'',
    'api_v1.ProjectResource':'',
    'api_v1.ProjectSchemaCollectorsResource':'',
    'api_v1.ProjectTablesResource':'',
    'api_v1.ProjectUserGlossariesResource':'',
    'api_v1.ProjectUserModelsResource':'',
    'api_v1.ProjectUserResource':'',
    'api_v1.ProjectUsersAdvSearch':'',
    'api_v1.ProjectUsersResource':'',
    'api_v1.SchemaCollectResultListResource':'',
    'api_v1.SchemaCollectResultResource':'',
    'api_v1.TermCodeInstancesResource':'',
    'api_v1.TermInfotypesResource':'',
    'api_v1.TermMasterInfotypesResource':'',
    'api_v1.TermMasterProjectCodeInstancesResource':'',
    'api_v1.UserResource':'',
    'board._notice_view': CHECK_LOGIN,
    'board._notice_write': CHECK_LOGIN,
    'board._qna_view': CHECK_LOGIN,
    'board._qna_write': CHECK_LOGIN,
    'board._post_delete': CHECK_PROJECT_MEMBER,
    'board._post_modify': CHECK_PROJECT_MEMBER,
    'board._post_replies_view': CHECK_PROJECT_MEMBER,
    'board._post_view': CHECK_PROJECT_MEMBER,
    'board._post_view': CHECK_PROJECT_MEMBER,
    'board._post_write': CHECK_PROJECT_MEMBER,
    'board._posts': CHECK_PROJECT_MEMBER,
    'board._summary_projectgroup_notice': CHECK_LOGIN,
    'board._summary_projectgroup_qna': CHECK_LOGIN,
    'board.download': CHECK_PROJECT_MEMBER,
    'board.post_view': CHECK_PROJECT_MEMBER,
    'board.posts': CHECK_PROJECT_MEMBER,
    'board.replysave': CHECK_PROJECT_MEMBER,
    'board._project_group_notices': CHECK_LOGIN,
    'board._project_group_qnas': CHECK_LOGIN,
    'codeset.codeset_codedel': 'check_project_termmgr',
    'codeset.codeset_modify': 'check_project_termmgr',
    'codeset.codeset_modify_json': 'check_project_termmgr',
    'codeset.codeset_new': 'check_project_termmgr',
    'codeset.codeset_reset': 'check_project_termmgr',
    'codeset.codeset_view': CHECK_PROJECT_MEMBER,
    'codeset.static': '',
    'erc.erc_instant_viewer': CHECK_NOTHING,
    'erc.erc_simple_viewer': CHECK_NOTHING,
    'erc.ercapp': CHECK_PROJECT_MEMBER,
    'erc.erdMgmt': CHECK_PROJECT_MODELER,
    'erc.get_current_lock_info': CHECK_PROJECT_MEMBER,
    'erc.get_Ent_Tbl_Dtl': CHECK_PROJECT_MEMBER,
    'erc.get_entity_list': CHECK_PROJECT_MEMBER,
    'erc.get_entity_name_subj_list': CHECK_PROJECT_MEMBER,
    'erc.get_entity_subj_list': CHECK_PROJECT_MEMBER,
    'erc.get_ercapp_erd': CHECK_PROJECT_MEMBER,
    'erc.get_erd_erc_format': CHECK_PROJECT_MEMBER,
    'erc.get_erd_erwin72_format': CHECK_PROJECT_MEMBER,
    'erc.get_file_subj_tree': CHECK_PROJECT_MEMBER,
    'erc.get_glossary_info': CHECK_PROJECT_MEMBER,
    'erc.get_glossary_object': CHECK_PROJECT_MEMBER,
    'erc.get_lock': CHECK_PROJECT_MEMBER,
    'erc.get_memo_content': CHECK_PROJECT_MEMBER,
    'erc.get_memo_list': CHECK_PROJECT_MEMBER,
    'erc.get_minimal_subj_tree': CHECK_PROJECT_MEMBER,
    'erc.get_table_name_subj_list': CHECK_PROJECT_MEMBER,
    'erc.get_model_history_dtl': CHECK_PROJECT_MEMBER,
    'erc.get_model_schema_diff': CHECK_PROJECT_MEMBER,
    'erc.get_model_subj_tree': CHECK_NOTHING,
    'erc.get_model_version_info': CHECK_PROJECT_MEMBER,
    'erc.get_simpleviewer_erd': CHECK_NOTHING,
    'erc.get_sjatree_version_info': CHECK_PROJECT_MEMBER,
    'erc.get_subj_tree': CHECK_NOTHING,
    'erc.get_unregistered_tables_view': CHECK_PROJECT_MEMBER,
    'erc.get_unused_entities_view': CHECK_PROJECT_MEMBER,
    'erc.parse_Uploaded_Erc_File': CHECK_PROJECT_MEMBER,
    'erc.parse_Uploaded_Erd_File': CHECK_PROJECT_MEMBER,
    'erc.release_lock': CHECK_PROJECT_MEMBER,
    'erc.rollback_model': CHECK_PROJECT_MEMBER,
    'erc.run_model_schema_compare': CHECK_PROJECT_MEMBER,
    'erc.save_ERD': CHECK_PROJECT_MODELER,
    'erc.save_memo': CHECK_PROJECT_MEMBER,
    'erc.set_subj_tree': CHECK_PROJECT_MEMBER,
    'erc.static': '',
    'erc.upload_erc_file': CHECK_PROJECT_MODELER,
    'erc.upload_erd_file': CHECK_PROJECT_MODELER,
    'erc.upload_excel_file': CHECK_PROJECT_MODELER,
    'exporter._exporter': CHECK_LOGIN,
    'exporter._run': CHECK_LOGIN,
    'exporter.static': '',
    'glossary._glossary_empty': CHECK_PROJECT_TERMMGR,
    'glossary._glossary_info_detail': CHECK_PROJECT_MEMBER,
    'glossary._glossary_list': CHECK_PROJECT_MEMBER,
    'glossary._glossary_new': CHECK_PROJECT_TERMMGR,
    'glossary._glossary_preference': CHECK_PROJECT_TERMMGR,
    'glossary._glossary_preference_codeset': CHECK_PROJECT_TERMMGR,
    'glossary._glossary_reports': CHECK_PROJECT_MEMBER,
    'glossary._glossary_reports_run': CHECK_PROJECT_TERMMGR,
    'glossary._glossary_view': CHECK_PROJECT_MEMBER,
    'glossary.glossary_del': CHECK_PROJECT_TERMMGR,
    'glossary.glossary_list': CHECK_PROJECT_MEMBER,
    'glossary.glossary_new': CHECK_PROJECT_TERMMGR,
    'glossary.glossary_preference': CHECK_PROJECT_TERMMGR,
    'glossary.glossary_reports': CHECK_PROJECT_MEMBER,
    'glossary.glossary_samplegen': CHECK_PROJECT_TERMMGR,
    'glossary.glossary_view': CHECK_PROJECT_MEMBER,
    'glossary.static': '',
    'glossary_master._glossary_derived_codeterm': CHECK_LOGIN,
    'glossary_master._glossary_derived_codeterm_del': CHECK_LOGIN,
    'glossary_master._glossary_derived_codeterm_new': CHECK_LOGIN,
    'glossary_master._glossary_derived_codeterm_update': CHECK_LOGIN,
    'glossary_master._glossary_derived_codeterms':'',
    # 'glossary_master._glossary_derived_del':'',
    'glossary_master._glossary_derived_info':'',
    'glossary_master._glossary_derived_info_detail':'',
    'glossary_master._glossary_derived_model_reports':'',
    'glossary_master._glossary_derived_model_reports_run':'',
    'glossary_master._glossary_derived_modify':'',
    'glossary_master._glossary_derived_new':'',
    'glossary_master._glossary_derived_nonstrdtermmap_new':'',
    'glossary_master._glossary_derived_nonstrdtermmap_update':'',
    'glossary_master._glossary_derived_nonstrdtermmaps':'',
    'glossary_master._glossary_derived_nonstrdterms':'',
    'glossary_master._glossary_derived_reports':'',
    'glossary_master._glossary_derived_reports_run':'',
    'glossary_master._glossary_derived_term_delete':'',
    'glossary_master._glossary_derived_term_master_view':'',
    'glossary_master._glossary_derived_term_new':'',
    'glossary_master._glossary_derived_term_request_view':'',
    'glossary_master._glossary_derived_term_requests':'',
    'glossary_master._glossary_derived_term_update':'',
    'glossary_master._glossary_derived_terms':'',
    'glossary_master._glossary_master_codeterm_new':'',
    'glossary_master._glossary_master_codeterm_update':'',
    'glossary_master._glossary_master_codeterms':'',
    'glossary_master._glossary_master_info':'',
    'glossary_master._glossary_master_info_detail':'',
    'glossary_master._glossary_master_infotype_new':'',
    'glossary_master._glossary_master_infotype_update':'',
    'glossary_master._glossary_master_infotypes':'',
    'glossary_master._glossary_master_preference':'',
    'glossary_master._glossary_master_preference_codeset':'',
    'glossary_master._glossary_master_reports':'',
    'glossary_master._glossary_master_reports_run':'',
    'glossary_master._glossary_master_term_delete':'',
    'glossary_master._glossary_master_term_new':'',
    'glossary_master._glossary_master_term_new_strdterm':'',
    'glossary_master._glossary_master_term_new_synonym':'',
    'glossary_master._glossary_master_term_new_unitterm':'',
    'glossary_master._glossary_master_term_request_review':'',
    'glossary_master._glossary_master_term_request_review_approve':'',
    'glossary_master._glossary_master_term_request_review_reject':'',
    'glossary_master._glossary_master_term_requests':'',
    'glossary_master._glossary_master_term_update':'',
    'glossary_master._glossary_master_term_view':'',
    'glossary_master._glossary_master_terms':'',
    'glossary_master._glossary_master_xlsloaderhistory':'',
    'glossary_master._glossary_master_xlsloaderhistorylist':'',
    'glossary_master._xlsloader':'',
    'glossary_master.codeset_modify_json': '',
    'glossary_master.codeset_reset': '',
    'glossary_master.codeset_view': '',
    'glossary_master.get_term_composition_list':'',
    'glossary_master.glossary_derived_c_xls':'',
    'glossary_master.glossary_derived_codeterm':'',
    'glossary_master.glossary_derived_codeterm_new':'',
    'glossary_master.glossary_derived_codeterm_update':'',
    'glossary_master.glossary_derived_codeterms':'',
    'glossary_master.glossary_derived_del':'',
    'glossary_master.glossary_derived_modify':'',
    'glossary_master.glossary_derived_nonstrdterm_new':'',
    'glossary_master.glossary_derived_nonstrdtermmap_update':'',
    'glossary_master.glossary_derived_nonstrdtermmaps':'',
    'glossary_master.glossary_derived_nonstrdterms':'',
    'glossary_master.glossary_derived_reports':'',
    'glossary_master.glossary_derived_t_xls':'',
    'glossary_master.glossary_derived_term_delete':'',
    'glossary_master.glossary_derived_term_master_view':'',
    'glossary_master.glossary_derived_term_new':'',
    'glossary_master.glossary_derived_term_request_view':'',
    'glossary_master.glossary_derived_term_requests':'',
    'glossary_master.glossary_derived_term_update':'',
    'glossary_master.glossary_derived_terms':'',
    'glossary_master.glossary_derived_upload_excel':'',
    'glossary_master.glossary_derived_view':'',
    'glossary_master.glossary_derived_xlsloaderhistory':'',
    'glossary_master.glossary_derived_xlsloaderhistorylist':'',
    'glossary_master.glossary_master':'',
    'glossary_master.glossary_master_c_xls':'',
    'glossary_master.glossary_master_codeterm_del':'',
    'glossary_master.glossary_master_codeterm_new':'',
    'glossary_master.glossary_master_codeterm_update':'',
    'glossary_master.glossary_master_codeterms':'',
    'glossary_master.glossary_master_empty':'',
    'glossary_master.glossary_master_i_xls':'',
    # 'glossary_master.glossary_master_infotype_delete':'',
    'glossary_master.glossary_master_infotype_new':'',
    'glossary_master.glossary_master_infotype_update':'',
    'glossary_master.glossary_master_infotypes':'',
    'glossary_master.glossary_master_preference':'',
    'glossary_master.glossary_master_reports':'',
    'glossary_master.glossary_master_samplegen':'',
    'glossary_master.glossary_master_t_xls':'',
    'glossary_master.glossary_master_term_new':'',
    'glossary_master.glossary_master_term_request_review':'',
    'glossary_master.glossary_master_term_requests':'',
    'glossary_master.glossary_master_term_update':'',
    'glossary_master.glossary_master_term_view':'',
    'glossary_master.glossary_master_terms':'',
    'glossary_master.glossary_master_xlsloaderhistory':'',
    'glossary_master.glossary_master_xlsloaderhistorylist':'',
    'glossary_master.static':'',
    'glossary_master.upload_excel':'',
    'glossary_master.validate_strdterm_name':'',
    'glossary_master.validate_unitterm_name':'',
    'infotype._glossary_infotype_new': CHECK_PROJECT_TERMMGR,
    'infotype._glossary_infotypes': CHECK_PROJECT_MEMBER,
    'infotype._modify_infotype': CHECK_PROJECT_TERMMGR,
    'infotype.get_infotype_xls': CHECK_PROJECT_MEMBER,
    'infotype.glossary_infotype_new': CHECK_PROJECT_TERMMGR,
    'infotype.glossary_infotypes': CHECK_PROJECT_MEMBER,
    'infotype.static':'',
    'infotype.validate_infotype_name': CHECK_PROJECT_TERMMGR,
    'integrity._model_schema_report': CHECK_PROJECT_MEMBER,
    'integrity.static':'',
    'login._change_password': 'login_required',
    'login._profile': 'login_required',
    'login._profile_edit': 'login_required',
    'login._report_subscription': 'login_required',
    'login.delete_profile_img': 'login_required',
    'login.dev_ops_login': '',
    'login.forget_password': '',
    'login.login': '',
    'login.logout': 'login_required',
    'login.password_verify': '',
    'login.profile': 'login_required',
    'login.profile_img': 'login_required',
    'login.profile_timg': 'login_required',
    'login.resend_verifying_mail': '',
    'login.signup': '',
    'login.static':'',
    'login.verify': '',
    'login.verify_guide': '',
    'model_mgmt._model_property': CHECK_PROJECT_MEMBER,
    'model_mgmt._model_version_lock': CHECK_PROJECT_MODELER,
    'model_mgmt.get_model_timeline': CHECK_PROJECT_MODELER,
    'model_mgmt.model_mgmt': CHECK_PROJECT_MODELER,
    'model_mgmt.static':'',
    'model_mgmt.timeline_remove_lock': CHECK_PROJECT_MODELER,
    'portal._project_billing_ksnet_rcv': 'login_required',
    'portal._projects_all': 'login_required',
    'portal._projects_mine': 'login_required',
    'portal._projects_picked': 'login_required',
    'portal._projects_recommend': 'login_required',
    'portal._projects_visited': 'login_required',
    'portal.about': '',
    'portal.default_project_group_index': '',
    'portal.dialog_dont_collect_emails': '',
    'portal.dialog_privacy_policy': '',
    'portal.dialog_privacy_policy_agree': '',
    'portal.dialog_toc': '',
    'portal.download_file':'',
    'portal.index': '',
    'portal.locale': '',
    'portal.manual': '',
    'portal.new_locale': '',
    'portal.projects_more': 'login_required',
    'portal.raise_503': '',
    'portal.raise_exception_test': '',
    'portal.search': 'login_required',
    'portal.services': '',
    'portal.static':'',
    'project._invite': CHECK_PROJECT_MEMBER,
    'project._invite_review': CHECK_PROJECT_MEMBER,
    'project._members': CHECK_PROJECT_MEMBER,
    'project._preference': CHECK_PROJECT_OWNER,
    'project._preference_for_projectgroup': '',
    'project._subjectarea_recently_changed':'',
    'project._subscribe':'',
    'project._subscription_ksnet_result': CHECK_PROJECT_OWNER,
    'project._subscription_log': CHECK_PROJECT_OWNER,
    'project._summary_board': CHECK_PROJECT_MEMBER,
    'project._summary_glossary': CHECK_PROJECT_MEMBER,
    'project._summary_model': CHECK_PROJECT_MEMBER,
    'project._summary_model_json': CHECK_PROJECT_MEMBER,
    'project.cancel_subscription': CHECK_PROJECT_OWNER,
    'project.convert_to_free': CHECK_PROJECT_OWNER,
    'project.create_project': 'login_required',
    'project.create_project_plus': CHECK_PROJECT_OWNER,
    'project.create_project_plus_coupon_result': CHECK_PROJECT_OWNER,
    'project.create_project_plus_result': CHECK_PROJECT_OWNER,
    'project.delegate_owner': CHECK_PROJECT_OWNER,
    'project.delete_profile_img': 'check_project_owner',
    'project.demo': '',
    'project.destroy': 'check_project_owner',
    'project.glossary_master_view': '',
    'project.index': CHECK_PROJECT_MEMBER,
    'project.join_request': '',
    'project.leave': CHECK_PROJECT_MEMBER,
    'project.member_role_action': CHECK_PROJECT_OWNER,
    'project.members': CHECK_PROJECT_MEMBER,
    'project.not_seen': '',
    'project.preference': 'check_project_owner',
    'project.profile_img': '',
    'project.profile_timg': '',
    'project.project_layout': CHECK_PROJECT_MEMBER,
    'project.static':'',
    'project.subscription': CHECK_PROJECT_OWNER,
    'project_group._info': 'login_required',
    'project_group._invite': 'login_required',
    'project_group._invite_review':'',
    'project_group._pg_subscription_ksnet_result':'',
    'project_group._pg_subscription_log':'',
    'project_group._preference_basic':'',
    'project_group._preference_glossaries':'',
    'project_group._preference_members': 'login_required',
    'project_group._preference_members_autoinvite': 'login_required',
    'project_group._preference_project':'',
    'project_group._preference_projects': 'login_required',
    'project_group._preference_security': 'login_required',
    'project_group._user_password_reset':'',
    'project_group._user_role_changer':'',
    'project_group.banner_img': 'login_required',
    'project_group.brand_img': 'login_required',
    'project_group.change_default_projectg': 'login_required',
    'project_group.delete_banner_img': 'login_required',
    'project_group.delete_brand_img': 'login_required',
    'project_group.index': 'login_required',
    'project_group.list_projects': 'login_required',
    'project_group.member_role_action':'',
    'project_group.pg_cancel_subscription':'',
    'project_group.pg_create_ksnet':'',
    'project_group.pg_create_ksnet_result':'',
    'project_group.pg_subscription':'',
    'project_group.preference': 'login_required',
    'project_group.preference_glossaries':'',
    'project_group.preference_join_rules': 'login_required',
    'project_group.preference_members': 'login_required',
    'project_group.preference_projects': 'login_required',
    'project_group.preference_security': 'login_required',
    'project_group.project_group_layout':'',
    'project_group.static': 'login_required',
    'project_group.user_leave': '',
    'project_group.validate_pg_slug': '',
    'projectuser._user_role_changer': CHECK_PROJECT_OWNER,
    'projectuser.static': CHECK_NOTHING,
    'projectuser.user_leave': CHECK_PROJECT_OWNER,
    'report._model_attributes': CHECK_PROJECT_MEMBER,
    'report._model_entities': CHECK_PROJECT_MEMBER,
    'report._model_glossary_report': CHECK_PROJECT_MEMBER,
    'report._model_glossary_report_run': CHECK_PROJECT_MEMBER,
    'report._model_report_info': CHECK_PROJECT_MEMBER,
    'report._model_scripts': CHECK_PROJECT_MEMBER,
    'report._model_validate_with_glossary': CHECK_PROJECT_MEMBER,
    'report.attr_detail': CHECK_PROJECT_MEMBER,
    'report.attr_report': CHECK_PROJECT_MEMBER,
    'report.create_script': CHECK_PROJECT_MEMBER,
    'report.entity_attr': CHECK_PROJECT_MEMBER,
    'report.entity_report': CHECK_PROJECT_MEMBER,
    'report.get_entities': CHECK_PROJECT_MEMBER,
    'report.get_model_list': CHECK_PROJECT_MEMBER,
    'report.get_subjectareas_list': CHECK_PROJECT_MEMBER,
    'report.model_attributes': CHECK_PROJECT_MEMBER,
    'report.model_entities': CHECK_PROJECT_MEMBER,
    'report.model_integrity': CHECK_PROJECT_MEMBER,
    'report.model_report': CHECK_PROJECT_MEMBER,
    'report.model_scripts': CHECK_PROJECT_MEMBER,
    'report.model_validate_with_glossary': CHECK_PROJECT_MEMBER,
    'report.static':'',
    'report.validate_strd': CHECK_PROJECT_MEMBER,
    'schema._collectors': CHECK_PROJECT_MODELER,
    'schema._model_delete_db_collector': CHECK_PROJECT_MODELER,
    'schema._model_modify_db_collector': CHECK_PROJECT_MODELER,
    'schema._model_schema_collect_exceptions': CHECK_PROJECT_MODELER,
    'schema._model_schema_collect_result_dtl': CHECK_PROJECT_MODELER,
    'schema._model_schema_collect_result_list': CHECK_PROJECT_MODELER,
    'schema._model_schema_compare_dtl': CHECK_PROJECT_MODELER,
    'schema.index': CHECK_PROJECT_MODELER,
    'schema.model_run_schema_collector': CHECK_PROJECT_MODELER,
    'schema.run_model_schema_compare': CHECK_PROJECT_MODELER,
    'schema.static':'',
    'schema.test_schema_collector_connection': CHECK_PROJECT_MODELER,
    'serve_js':'',
    'spec':'',
    'static':'',
    'static_from_root':'',
    'term._codeterm_search': CHECK_PROJECT_MEMBER,
    'term._glossary_terms': CHECK_PROJECT_MEMBER,
    'term._term_delete': CHECK_PROJECT_MEMBER,
    'term._term_process_approve': CHECK_PROJECT_TERMMGR,
    'term._term_process_cancel': CHECK_PROJECT_MEMBER,
    'term._term_process_reject': CHECK_PROJECT_TERMMGR,
    'term._term_regist': CHECK_PROJECT_MEMBER,
    'term._term_update': CHECK_PROJECT_MEMBER,
    'term._term_view': CHECK_PROJECT_MEMBER,
    'term._xlsloaderhistory': CHECK_PROJECT_TERMMGR,
    'term._xlsloaderhistorylist': CHECK_PROJECT_TERMMGR,
    'term.code_instance': CHECK_PROJECT_MEMBER,
    'term.code_instance_excel_parsing': CHECK_PROJECT_MEMBER,
    'term.get_term_composition_list': CHECK_PROJECT_MEMBER,
    'term.get_term_excel': CHECK_PROJECT_MEMBER,
    'term.glossary_terms': CHECK_PROJECT_MEMBER,
    'term.static':'',
    'term.strd_term_excel_parsing': CHECK_PROJECT_TERMMGR,
    'term.term_regist': CHECK_PROJECT_MEMBER,
    'term.term_update': CHECK_PROJECT_MEMBER,
    'term.term_update': CHECK_PROJECT_MEMBER,
    'term.term_view': CHECK_PROJECT_MEMBER,
    'term.unit_term_excel_parsing': CHECK_PROJECT_TERMMGR,
    'term.upload_excel': CHECK_PROJECT_TERMMGR,
    'term.upload_excel_infotype_parse': CHECK_PROJECT_TERMMGR,
    'term.validate_code_id': CHECK_PROJECT_MEMBER,
    'term.validate_strdterm_name': CHECK_PROJECT_MEMBER,
    'term.validate_strdterm_physical_name': CHECK_PROJECT_MEMBER,
    'term.validate_unitterm_name': CHECK_PROJECT_MEMBER,
    'term.validate_unitterm_physical_name': CHECK_PROJECT_MEMBER,
    'term.xlsloaderhistory': CHECK_PROJECT_TERMMGR,
    'term.xlsloaderhistorylist': CHECK_PROJECT_TERMMGR,
}  # noqa


def _context_user():
    if current_user.is_anonymous:
        return None
    return current_user._get_current_object()


def _context_project_group():
    return g.project_group


def _context_project():
    return g.project


def _context_glossary():
    return g.glossary


def is_pg_owner():
    '''current_user가 project_group_owner인지 체크'''
    return _context_user() is not None and \
        ProjectGroupUser.objects(
            project_group=_context_project_group(),
            user=_context_user(),
            is_owner=True).first() is not None


can_be_pg_owner = is_pg_owner


def is_pg_moderator():
    '''current_user가 project_group_moderator인지를 체크'''
    return _context_user() is not None and \
        ProjectGroupUser.objects(
            project_group=_context_project_group(),
            user=_context_user(),
            is_moderator=True
    ).first() is not None


def can_be_pg_moderator():
    '''current_user가 project_group_moderator인지를 체크'''
    return _context_user() is not None and \
        ProjectGroupUser.objects(
            project_group=_context_project_group(),
            user=_context_user()
    ).filter(
        Q(is_moderator=True) |
        Q(is_owner=True)
    ).first() is not None


def is_pg_termer():
    '''current_user가 project_group_termer인지를 체크'''
    return _context_user() is not None and \
        ProjectGroupUser.objects(
            project_group=_context_project_group(),
            user=_context_user(),
            is_termer=True
    ).first() is not None


def can_be_pg_termer():
    return can_be_pg_moderator() or is_pg_termer()


def is_p_owner():
    return _context_user() is not None and \
        ProjectUser.objects(
            project=_context_project(),
            user=_context_user(),
            is_owner=True
    ).first() is not None


can_be_p_owner = is_p_owner


def is_p_termer(glossary_obj=None):

    glossary = glossary_obj
    if not glossary:
        try:
            glossary = _context_glossary()
        except:  # noqa
            pass

    return _context_user() is not None and \
        ProjectUser.objects(
            Q(project=_context_project()) &
            Q(user=_context_user()) &
            Q(is_termer=True) &
            (
                Q(manageable_glossaries=glossary) |
                Q(can_manage_all_glossaries=True)
            )
    ).first() is not None


def can_be_p_termer(glossary_obj=None):
    return is_p_owner() or is_p_termer(glossary_obj)


def is_p_modeler(model_obj=None):
    q = (
        Q(project=_context_project()) &
        Q(user=_context_user()) &
        Q(is_modeler=True)
    )
    if model_obj == 'all':
        q = q & Q(can_manage_all_models=True)
    elif model_obj is None:
        pass
    else:
        q = q & (
            (Q(manageable_models=model_obj.root_object) if model_obj else True) |
            Q(can_manage_all_models=True)
        )

    return _context_user() is not None and \
        ProjectUser.objects(q).first() is not None


def can_be_p_modeler(model_obj=None):
    return is_p_owner() or is_p_modeler(model_obj)


def is_p_member():
    return _context_user() is not None and \
        ProjectUser.objects(
            project=_context_project(),
            user=_context_user()
    ).first() is not None
