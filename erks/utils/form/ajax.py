import mongoengine

from flask_admin._compat import string_types, as_unicode
# from flask_admin._compat import as_unicode
from flask_admin.model.ajax import AjaxModelLoader, DEFAULT_PAGE_SIZE
# from flask import g


# def register_loader(loader_name, loader):
#     if hasattr(g, 'form_ajax_refs') and isinstance(g.form_ajax_refs, dict):
#         if loader_name in g.form_ajax_refs:
#             # raise Exception('already registered loader')
#             pass
#     else:
#         g.form_ajax_refs = dict()

#     g.form_ajax_refs[loader_name] = loader


class QueryAjaxModelLoader(AjaxModelLoader):
    def __init__(self, name, model, **options):
        super(QueryAjaxModelLoader, self).__init__(name, options)

        self.model = model
        self.fields = options.pop('fields', [])
        self.label_attr = options.pop('label_attr', None)
        # self.data_url = options.get('data_url')

        self.options = options
        # if len(options):
        #     self.query_string = urlencode(OrderedDict(**self.options))
        # else:
        #     self.query_string = ""

        self._cached_fields = self._process_fields()

        if not self.fields:
            raise ValueError('AJAX loading requires `fields` to be specified for %s.%s' % (model, self.name))

    def _process_fields(self):
        remote_fields = []

        for field in self.fields:
            if isinstance(field, string_types):
                attr = getattr(self.model, field, None)

                if not attr:
                    raise ValueError('%s.%s does not exist.' % (self.model, field))

                remote_fields.append(attr)
            else:
                remote_fields.append(field)

        return remote_fields

    def format(self, model):
        if not model:
            return None

        if self.label_attr:
            label = getattr(model, self.label_attr)
        else:
            label = as_unicode(model)
        return (as_unicode(model.id), label)

    def get_one(self, pk):
        return self.model.objects.filter(id=pk).first()

    def get_list(self, term, offset=0, limit=DEFAULT_PAGE_SIZE):
        query = self.model.objects

        criteria = None

        # HACK: True/False checking is not impossible;;
        options_processed = self.options

        if options_processed:
            query = query.filter(**options_processed)

        for field in self._cached_fields:
            flt = {u'%s__icontains' % field.name: term}

            if not criteria:
                criteria = mongoengine.Q(**flt)
            else:
                criteria |= mongoengine.Q(**flt)

        query = query.filter(criteria)

        if offset:
            query = query.skip(offset)

        return query.limit(limit).all()
