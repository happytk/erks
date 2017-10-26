# -*- encoding: utf-8-*-
from wtforms import (
    Field,
)
from wtforms.widgets import HiddenInput
from flask_mongoengine.wtf.fields import (
    QuerySetSelectField as FlaskAdminQuerySetSelectField)
from flask_admin.model.fields import AjaxSelectField
from .ajax import QueryAjaxModelLoader
from .widgets import AjaxSelect2Widget
from flask import g


class QuerySetSelectField(FlaskAdminQuerySetSelectField):
    def __init__(self, label=u'', validators=None, queryset=None, label_attr='',
                 allow_blank=False, blank_text=u'---', **kwargs):
        if queryset is not None and callable(queryset):
            queryset = queryset()

        super(QuerySetSelectField, self).__init__(label, validators, queryset, label_attr,
                                                  allow_blank, blank_text, **kwargs)


class AjaxQuerySetSelectField(AjaxSelectField):
    def __init__(self, label=u'', validators=None, queryset=None, label_attr='',
                 search_fields=[],
                 loader_name=u'',
                 allow_blank=False, blank_text=u'---', **kwargs):
        if queryset is not None and callable(queryset):
            queryset = queryset()

        loader = QueryAjaxModelLoader(loader_name, queryset, fields=search_fields, label_attr=label_attr)
        super(AjaxQuerySetSelectField, self).__init__(loader, label, validators, allow_blank, blank_text, **kwargs)


class AjaxLoaderSelectField(AjaxSelectField):
    """
    AjaxQuerySetSelectField는 queryset을 field에도 넣어주고 같은 내용의 query를
    ajax데이터를 조회하는 view에서도 동일하게 구현해야 한다.
    이 중복되는 부분을 loader로 지정하고, loader-name으로 양쪽에서 참조할 수 있도록 구현.

    loader는 g에 정의한다.
    이 구현방법에는 문제가 있다.
    - project_id, glossary_id, term_id와 같은 조회조건들을 넘겨줘야 하는데,
    - loader자체로 넘겨줄 수 있는 방법이 없고,
    - 지정한 view에 건네주기도 어렵다.

    그래서 field자체에 양쪽에 건네줄 param을 지정해서 넘겨준다면?
    - parameter로 받은 내용을 loader와 결합시키고,
    - parameter로 받은 내용을 view에도 args로 전달한다.
    - 그러면 view에서 loader와 마찬가지로 결합시킨다.

    위 방법도 문제가 있다.
    - parameter는 mongoengine에서 reference를 찾을때 쓸 수 없다.
    """

    # flask_admin에서 제공하는 ajaxselect2widget이
    # view-url을 customized할 수 없으므로 자체구현한 것으로 대체
    widget = AjaxSelect2Widget()

    def __init__(self,
                 label=u'',
                 validators=None,
                 loader_name=u'',
                 allow_blank=False,
                 blank_text=u'---',
                 **kwargs):
        loader = g.form_ajax_refs.get(loader_name)
        super(AjaxLoaderSelectField, self).__init__(
            loader, label, validators,
            allow_blank, blank_text, **kwargs)


class ReferenceField(Field):

    """flask-mongoengine의 reference type 필드는 select로 변환되기 때문에
    object-id를 hidden으로 관리하는 경우를 위해 구현.
    """

    widget = HiddenInput()

    def __init__(self, label=u'', validators=None, model=None, **kwargs):
        super(ReferenceField, self).__init__(label, validators, **kwargs)
        self.model = model

    def process_formdata(self, valuelist):
        """
        field의 data는 view나 form에서 접근하는 데이터이므로
        실제 db에서 가져온 document를 가지고 있어야 한다.
        """
        if valuelist and valuelist[0]:
            self.data = self.model.objects(id=valuelist[0]).first()
        else:
            self.data = None

    def _value(self):
        """_value()의 리턴값은 widget의 value값을 얻을때 호출되는 값이다.
        그러므로 여기서는 id를 리턴하는 것이 합리적으로 보인다.
        self.data는 문자열로 변환시 __repr__로 호출되어 id가 아닌 값이 될 수 있기 때문

        이 부분을 self.data로 하면 ReferenceField를 사용하는 Model은
        무조건 __repr__을 id를 리턴하도록 구현해야 문제없이 동작하게 된다.
        """
        if self.data:
            return str(self.data.id)
            # return self.data
        else:
            return u''


class SelectReferenceField(ReferenceField):
    def iter_choices(self):
        return []


class ReferenceFieldList(Field):
    widget = HiddenInput()

    def __init__(self, label=u'', validators=None, model=None, **kwargs):
        kwargs['default'] = []
        super(ReferenceFieldList, self).__init__(label, validators, **kwargs)
        self.model = model

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [self.model.objects(id=value).first() for value in valuelist]
            self.data = list(filter(lambda x: x is not None, self.data))
        else:
            self.data = []

    def _value(self):
        if self.data:
            return [str(obj.id) for obj in self.data]
        else:
            return []


class CommaSeperatedReferenceField(Field):
    widget = HiddenInput()

    def __init__(self, label=u'', validators=None, model=None,
                 distinct=True,
                 query_key="id", additional_queries=None,
                 query_func=None,
                 **kwargs):
        kwargs['default'] = []
        super(CommaSeperatedReferenceField, self).__init__(label, validators, **kwargs)
        self.model = model
        self.query_key = query_key
        self.additional_queries = additional_queries
        self.distinct = distinct
        self.query_func = query_func

    def process_formdata(self, valuelist):
        # hack: select2에서 데이타를 ['', 'email'] 요런식으로 던져준다.
        # 앞쪽 어딘가에 form field가 하나 더 있는 것처럼 동작
        valuelist = list(filter(lambda x: len(x), valuelist))

        if valuelist and valuelist[0]:
            ids = [x.strip() for x in valuelist[0].split(',')]
            if self.distinct:
                seen = set()
                seen_add = seen.add
                ids = [x for x in ids if not (x in seen or seen_add(x))]
                # ids = list(set(ids)) # 이 상황이 순서를 바꿔버릴 수 있다.
                # ids = []
            self.raw_data = ids
            self.data = []
            if self.query_func:
                for id_str in ids:
                    try:
                        self.data.append(self.query_func(self.model.objects, id_str))
                    except self.model.DoesNotExist:
                        pass
            else:
                for id_str in ids:
                    q = {self.query_key: id_str}
                    if self.additional_queries:
                        q.update(self.additional_queries)
                    self.data.append(
                        self.model.objects(**q).first()
                    )
            self.data = list(filter(lambda x: x is not None, self.data))
        else:
            self.raw_data = []
            self.data = []

    def _value(self):
        if self.data:
            if isinstance(self.data[0], self.model):
                return u','.join([str(t[self.query_key]) for t in self.data])
            else:
                return u','.join(self.data)
        else:
            return u''
