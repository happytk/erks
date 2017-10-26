# -*- encoding:utf-8 -*-

# api(v1) specification

# /glossary/:id/domains

from flask.views import MethodView as Resource

from mongoengine import Q
from flask import jsonify, current_app, request
from flask import Blueprint
from ercc.models import (
    Glossary,
    # Term,
)
import json

API_PREFIX = '/api_select2'


class ListResource(Resource):

    '''resource_cls or queryset() have to be provided.'''

    exclude_fields = []
    dynamic_fields = []

    def queryset(self, pk):
        return self.resource_cls.objects(pk=pk)

    def response_headers(self):
        return dict()

    def search(self, query_string=''):
        return self

    def get(self, id):
        # args
        offset = int(request.args.get('offset', 0))
        limit = int(request.args.get('limit', 10))
        # sorted_ = request.args.get('sort', '')  # +field1,-field2
        # order = request.args.get('order', 'asc')
        # filter_ = request.args.get('filter', None)  # filters={"hello":"world"}
        search = request.args.get('q', None)  # unified_search_text
        # fields = request.args.get('fields', None)  # field1,field2,field3 ..

        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()

        query = self.queryset(id)

        # if fields:
        #     query = query.only(*fields.split(','))
        # else:
        #     query = query.exclude(*self.exclude_fields)

        # if filter_:
        #     from json import loads
        #     search_filters = loads(filter_)
        #     for key, value in search_filters.items():
        #         query = query.filter(**{key + '__icontains': value})

        # if sorted_ and order == 'desc':
        #     sorted_ = '-' + sorted_

        if search:
            query = self.search(query, search_string=search)

        return self._yield(
            query,
            offset=offset,
            limit=limit)

    def _yield(self, query, offset=0, limit=10, sorted_=''):
        total_count = query.count()
        # # temporary new fields for json-output
        # models = ', '.join(
        #     obj.to_json()
        #     for obj in Model.objects(
        #         prjId=str(pu.project.id)).only('name').all())
        # models = json.loads('[{}]'.format(models))
        # mm_ids = [str(g.id) for g in pu.manageable_models]
        # for model in models:
        #     model["is_my_model"] = model["id"] in mm_ids

        def gen():
            ret = []
            for obj in query.order_by(sorted_).skip(offset).limit(limit):
                ret.append(
                    json.dumps(dict(id=str(obj.id), text=obj.term_name),
                               ensure_ascii=False))
            yield '{"results": [%s]}' % (','.join(ret))

        headers = {
            'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            gen(),
            headers=headers,
            mimetype='application/json')


class SingleResource(Resource):
    exclude_fields = []

    def get(self, id):
        queryset = self.resource_cls.objects
        if self.exclude_fields:
            queryset = queryset.exclude(*self.exclude_fields)
        return jsonify(json.loads(queryset.get_or_404(id=id).to_json()))


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
# /glossary/:id/entities

class GlossaryDomainsResource(ListResource):

    exclude_fields = ['glossary', 'project', 'project_group',
                      'created_by', 'published_by', 'modified_by',
                      'requested_by', 'composition', 'domain',
                      'code_instances', 'infotypes']
    dynamic_fields = ['is_ongoing', 'is_referred']

    input_cls = Glossary

    def queryset(self, id):
        glossary = Glossary.head_objects.get_or_404(id=id)
        return glossary.queryset_domainterm

    def search(self, query, search_string):
        return query.filter(Q(term_name__icontains=search_string))


def configure_api_select2(app):
    def _(uri):
        return API_PREFIX + uri

    api = Blueprint('api_select2', __name__)

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
    api.add_url_rule(
        _('/glossary/<mbj:id>/domains'),
        view_func=GlossaryDomainsResource.as_view('GlossaryDomainsResource'))

    app.register_blueprint(api)
