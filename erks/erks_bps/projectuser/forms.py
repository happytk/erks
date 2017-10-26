# -*- encoding:utf8 -*-
from flask import g
from flask_mongoengine.wtf import model_form
# from erks.erks_bps.glossary.models import GlossaryBase
# from erks.erks_bps.erc.models import Model
from erks.utils.form.fields import CommaSeperatedReferenceField
from erks.erks_bps.projectuser.models import (
    ProjectUser
)
from wtforms import (
    # Form,
    # TextField,
    # SelectField,
    # FileField,
    # HiddenField,
    # validators,
    BooleanField,
    # widgets,
)
from flask_babel import lazy_gettext
from bson import ObjectId
from supports import wtformsparsleyjs

EmailField = wtformsparsleyjs.EmailField
TextField = wtformsparsleyjs.StringField
SelectField = wtformsparsleyjs.SelectField


# class ProjectUserModelsForm(model_form(ProjectUser, only=(
#                             'manageable_models', 'can_manage_all_models'))):
#     manageable_models = CommaSeperatedReferenceField(model=Model)


# class ProjectUserGlossariesForm(model_form(
#         ProjectUser,
#         only=('manageable_glossaries', 'can_manage_all_glossaries'))):
#     manageable_glossaries = CommaSeperatedReferenceField(model='Glossary')


class ProjectUserRoleForm(model_form(
        ProjectUser,
        only=(
            'is_modeler',
            'is_termer',
            'manageable_glossaries',
            'can_manage_all_glossaries',
            'manageable_models',
            'can_manage_all_models'))):
    is_modeler = BooleanField(u'모델러 지정')
    is_termer = BooleanField(u'용어관리자 지정')
    # can_manage_all_glossaries = BooleanField(
    #     label=lazy_gettext(u'전체용어사전 관리'),
    #     description=lazy_gettext(
    #         u'전체 용어집에 대해서 관리자 권한 부여'
    #         u'(신규 용어집에 대한 생성권한 및 이후에 생성되는 용어집에 대한 권한을 포함합니다.)'))
    # can_manage_all_models = BooleanField(
    #     label=lazy_gettext(u'전체모델 관리'),
    #     description=lazy_gettext(
    #         u'전체 ER-D모델에 대해서 관리자 권한 부여'
    #         u'(신규 모델에 대한 생성권한 및 이후에 생성되는 모델에 대한 권한을 포함합니다.)'))
    # manageable_glossaries = CommaSeperatedReferenceField(model=GlossaryBase)
    # manageable_models = CommaSeperatedReferenceField(
    #     model=Model,
    #     query_func=lambda queryset, v: queryset.filter(newest='Y', Oid=ObjectId(v), prjId=str(g.project.id)).get().root_object
    # )

    def populate_my_glossaries(self):
        # temporary new fields for json-output
        project = g.project
        mg_ids = [str(g.id) for g in self.manageable_glossaries.data]
        return [
            (obj, str(obj.id) in mg_ids) for obj in GlossaryBase.head_objects(
                project=project).only('glossary_name').all()
        ]

    def populate_my_models(self):
        # temporary new fields for json-output
        project = g.project
        # import pdb; pdb.set_trace()
        mg_ids = [str(m.Oid) for m in self.manageable_models.data]
        return [
            (obj, str(obj.Oid) in mg_ids) for obj in Model.head_objects(
                prjId=str(project.id)).only('name', 'Oid').all()
        ]
