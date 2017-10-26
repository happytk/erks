# -*- coding: utf-8 -*-
import json
import logging as logger
from datetime import datetime

from flask_login import current_user
from flask import current_app
from mongoengine_goodjson.document import Helper
from bson import DBRef
from mongoengine import (
    ReferenceField,
    ListField,
    DoesNotExist,
)
import mongoengine
from erks.extensions import db


def current_user_or_none():
    if current_user and current_user.is_active:
        return current_user._get_current_object()
    else:
        '''anonymous user'''
        return None


def _patched_follow_reference(self, max_depth, current_depth,
                              use_db_field, data, *args, **kwargs):
    from mongoengine_goodjson.fields import FollowReferenceField
    ret = {}
    for fldname in self:
        fld = self._fields.get(fldname)
        is_list = isinstance(fld, db.ListField)
        target = fld.field if is_list else fld

        if all([
            isinstance(
                target, (db.ReferenceField, db.EmbeddedDocumentField)
            ), not isinstance(target, FollowReferenceField)
        ]):
            value = None
            ckwargs = kwargs.copy()
            if issubclass(target.document_type, Helper):
                ckwargs.update({
                    "follow_reference": True,
                    "max_depth": max_depth,
                    "current_depth": current_depth + 1,
                    "use_db_field": use_db_field
                })
            if is_list:
                value = []
                for doc in getattr(self, fldname, []):
                    tdoc = target.document_type.objects(
                        id=doc.id
                    ).get() if isinstance(doc, DBRef) else doc
                    dct = json.loads(tdoc.to_json(
                        *args, **ckwargs
                    )) if issubclass(
                        target.document_type, Helper
                    ) else tdoc.to_mongo()
                    if "_id" in dct:
                        dct["id"] = dct.pop("_id")
                    value.append(dct)
            else:
                # Honestly, I don't feel this implementation is good.
                # However, as #892 at MongoEngine
                # (https://github.com/MongoEngine/mongoengine/issues/892)
                # shows, to keep follow reference, this is only the way...
                #
                # (Of course, PR is appreciated.)
                try:
                    doc = getattr(self, fldname, None)
                except db.DoesNotExist:
                    doc = self._fields[fldname].document_type.objects(
                        id=data[fldname]
                    ).get()
                tdoc = target.document_type.objects(
                    id=doc.id
                ).get() if isinstance(doc, DBRef) else doc
                if tdoc:
                    value = json.loads(
                        tdoc.to_json(*args, **ckwargs)
                    ) if issubclass(
                        target.document_type, Helper
                    ) else tdoc.to_mongo() if doc else doc
                    if value and "_id" in value:
                        value["id"] = value.pop("_id")
                else:
                    value = None
            if value is not None:
                ret[fldname] = value
                # ret.update({fldname: value})
    return ret


JsonifyPatchMixin = Helper
JsonifyPatchMixin._follow_reference = _patched_follow_reference


class ArchivableDocument(db.Document):
    '''archive해야하는 document는 이 abstract-document를
    상속하면 자동으로 기존 collection-name 뒤에 -archive를 붙여서 저장한다.
    기존의 _id는 _oid로 대체시킨다. _action(update, delete)도 저장한다.'''

    meta = {
        'abstract': True
    }

    def archive(self, action):
        # building archive-collection
        dbname = current_app.config['MONGODB_SETTINGS']['DB']

        collection = self._get_collection()
        collection_name = f'{collection.name}_archive'

        a_collection = db.connection[dbname][collection_name]

        # building archive-data
        data = self.to_mongo()
        data['_oid'] = data.pop('_id')
        data['_action'] = action

        # save!
        a_collection.insert_one(data)

    def save(self, *args, **kwargs):
        ret = super(ArchivableDocument, self).save(*args, **kwargs)
        if kwargs.get('archiving', False):
            self.archive(action='update')
        else:
            typ = str(type(self))
            logger.debug(f'skipped to archive {typ}-{self.id}')
        return ret

    def delete(self, *args, **kwargs):
        '''삭제는 사실 action빼고는 특별히 의미는 없다.
        중복된 데이터가 쌓일 뿐이라서 빼도 무방해보임.'''
        ret = super(ArchivableDocument, self).delete(*args, **kwargs)
        if kwargs.get('archiving', False):
            self.archive(action='delete')
        return ret


class ReferenceValidatorMixin(object):
    def validate_reference_integrity(self):
        '''현재 document 객체의 reference field 유효성을 검사합니다.
        삭제된 doc을 reference하고 있는 field를 접근할 경우
        DoesNotExist오류가 발생하기 때문.

        다만 모든 ref-field를 풀어놓고 검사하기 때문에,(no_dereference하지 않음)
        전체 doc을 대상으로 이 함수를 이용하여 검사하려면 속도상 문제가 있음

        :return: 문제가 있는 필드이름의 목록을 return합니다.
        '''
        ref_error_fields = []
        for key, field in self._fields.items():
            if isinstance(field, ReferenceField):
                try:
                    getattr(self, key)
                except DoesNotExist:
                    ref_error_fields.append(key)
            elif isinstance(field, ListField):
                # listfield의 실제 속성을 meta에서 확인이 어려워서 일단 모두 검사
                if any(_ for _ in getattr(self, key) if isinstance(_, DBRef)):
                    ref_error_fields.append(key)

        return ref_error_fields


class AuditableMixin(object):
    created_by = db.ReferenceField(
        'User',
        default=current_user_or_none,
        reverse_delete_rule=mongoengine.NULLIFY)
    created_at = db.DateTimeField(default=datetime.now, required=True)
    modified_by = db.ReferenceField(
        'User',
        default=current_user_or_none,
        reverse_delete_rule=mongoengine.NULLIFY)
    modified_at = db.DateTimeField(default=datetime.now, required=True)

    def clean_by_auditable_mixin(self):
        self.modified_at = datetime.now()
        self.modified_by = current_user_or_none()


class JsonTransferableMixin(object):
    '''json으로 data-exchange할 수 있는 mixin인데..
    glossary-term전용으로 만들었음. 좀 더 일반화하자.'''

    def export_to_json(self):
        from erks.erks_bps.infotype.models import InfoType
        from erks.erks_bps.term.models import (
            UnitTerm,
            StrdTerm,
            Synonym
        )
        from erks.erks_bps.glossary.models import CodeSet

        pg_kwargs = dict(glossary=self)
        ret = {
            'glossary': self.to_json(),
            'codesets': [json.loads(c.to_json()) for c in CodeSet._all(**pg_kwargs) if c.is_clone],
            'infotypes': [json.loads(i.to_json()) for i in InfoType.objects(**pg_kwargs)],
            'unitterms': [json.loads(t.to_json()) for t in UnitTerm.objects(**pg_kwargs)],
            'strdterms': [json.loads(t.to_json()) for t in StrdTerm.objects(**pg_kwargs)],
            'synonyms': [json.loads(t.to_json()) for t in Synonym.objects(**pg_kwargs)],
        }
        return json.dumps(ret)

    def import_from_json(self, data):

        # empty-glossary
        from erks.erks_bps.glossary.models import CodeSet
        from erks.erks_bps.infotype.models import InfoType
        from erks.erks_bps.term.models import (
            UnitTerm,
            StrdTerm,
            Synonym,
            Term
        )

        CodeSet.objects(glossary=self).delete()
        InfoType.objects(glossary=self).delete()

        id_maps = {}

        def save_and_archive_old_id(doc):
            old_id = str(doc.id)
            del doc.id
            doc.save()
            new_id = str(doc.id)
            id_maps[old_id] = new_id
            current_app.logger.debug('switching {} -> {}'.format(old_id, new_id))
            return doc

        def switch_rep_infotype(doc):
            if doc.rep_infotype:
                new_id = id_maps[str(doc.rep_infotype.id)]
                doc.rep_infotype = InfoType.objects.get(id=new_id)

        def switch_infotypes(doc):
            if doc.infotypes:
                doc.infotypes = [
                    InfoType.objects.get(id=id_maps[str(infotype.id)]) for infotype in doc.infotypes
                ]

        def switch_domain(doc):
            if doc.domain:
                doc.domain = Term.objects.get(id=id_maps[str(doc.domain.id)])

        def switch_composition(doc):
            if doc.composition:
                doc.composition = [
                    Term.objects.get(id=id_maps[str(term.id)]) for term in doc.composition
                ]

        def switch_code_entity(doc):
            if doc.code_entity:
                doc.code_entity = None
                current_app.logger.debug('code_entity reference({})'
                                         ' will be loss.'.format(doc.code_entity.id))

        def switch_super_code(doc):
            if doc.super_code:
                doc.super_code = StrdTerm.objects.get(id=id_maps[str(doc.super_code.id)])

        def switch_rep_unitterm(doc):
            if doc.rep_unit_term:
                doc.rep_unit_term = Term.objects.get(id=id_maps[str(doc.rep_unit_term.id)])

        def switch_multiple_codes(doc):
            if doc.multiple_codes:
                doc.multiple_codes = [
                    StrdTerm.objects.get(id=id_maps[str(term.id)]) for term in doc.multiple_codes
                ]

        data = json.loads(data)
        for cs in data['codesets']:
            new_cs = CodeSet.from_json(json.dumps(cs))
            new_cs.project = self.project
            new_cs.glossary = self
            save_and_archive_old_id(new_cs)

        for record in data['infotypes']:
            new_i = InfoType.from_json(json.dumps(record))
            new_i.project = self.project
            new_i.glossary = self
            save_and_archive_old_id(new_i)

        for record in data['unitterms']:
            new_t = UnitTerm.from_json(json.dumps(record))
            new_t.project = self.project
            new_t.glossary = self
            switch_rep_infotype(new_t)
            switch_infotypes(new_t)
            save_and_archive_old_id(new_t)

        for record in data['strdterms']:
            new_t = StrdTerm.from_json(json.dumps(record))
            new_t.project = self.project
            new_t.glossary = self
            switch_rep_infotype(new_t)
            switch_composition(new_t)
            switch_code_entity(new_t)
            switch_super_code(new_t)
            switch_multiple_codes(new_t)
            switch_domain(new_t)
            save_and_archive_old_id(new_t)

        for record in data['synonyms']:
            new_t = Synonym.from_json(json.dumps(record))
            new_t.project = self.project
            new_t.glossary = self
            switch_rep_unitterm(new_t)
            save_and_archive_old_id(new_t)
