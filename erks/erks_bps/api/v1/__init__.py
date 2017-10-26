from flask.views import MethodView as Resource
from flask import jsonify, current_app, request, stream_with_context

import json
import mongoengine


def api_gen(iterable, **additional_info):
    yield '{'
    for key, value in additional_info.items():
        yield f'"{key}":'
        if isinstance(value, int):
            yield f'{value},'
        else:
            yield f'"{value}",\n'
    yield '"rows": ['
    entity_gen = iter(iterable)
    try:
        prev = next(entity_gen)  #
    except StopIteration:
        pass
    else:
        for entity in entity_gen:
            yield json.dumps(prev, indent=True, ensure_ascii=False)
            yield ', '
            prev = entity
        yield json.dumps(prev, indent=True, ensure_ascii=False)
    yield ']'
    yield '}'


class ListResource(Resource):

    '''resource_cls or queryset() have to be provided.'''

    exclude_fields = []
    dynamic_fields = []

    def queryset(self):
        return self.resource_cls.objects

    def response_headers(self):
        return dict()

    def search(self, query_string=''):
        return self

    def get(self):
        fields = request.args.get('fields', None)  # field1,field2,field3 ..
        filter_ = request.args.get('filter', None)  # filters={"hello":"world"}
        limit = request.args.get('limit', 10, int)
        offset = request.args.get('offset', 0, int)
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text
        sorted_ = request.args.get('sort', '')  # +field1,-field2

        query = self._build_queryset(
            self.queryset(),
            search=search,
            fields=fields,
            filter_=filter_,
            sorted_=sorted_,
            order=order,
        )
        total_count = query.count()
        headers = {
            'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())

        gen = self._yield(query, offset=offset, limit=limit, fields=fields)
        # if self.dynamic_fields:
        #     # url_for와 같은 action은 response에서 수행하면
        #     # application-context가 나간 후라서 call자체가 안된다.
        #     gen = list(gen)

        return current_app.response_class(
            stream_with_context(api_gen(
                gen,
                total=total_count,
            )),
            headers=headers,
            mimetype='application/json')

    def _build_queryset(self, query, search=None, fields=None, filter_=None, sorted_=None, order='asc'):
        # args
        # current_app.logger.debug(request.args)
        # import pdb; pdb.set_trace()

        if fields:
            fields = fields.split(',')
            query = query.only(*fields)
        else:
            # excludes를 유연하게 처리하도록
            if query.fields():
                exclude_fields = list(
                    set(query.fields()[0]._fields.keys()) &
                    set(self.exclude_fields)
                )
            else:
                exclude_fields = self.exclude_fields
            query = query.exclude(*exclude_fields)

        if filter_:
            from json import loads
            search_filters = loads(filter_)
            for key, value in search_filters.items():
                query = query.filter(**{key + '__icontains': value})

        if search:
            query = self.search(query, search_string=search)

        if sorted_ and order == 'desc':
            sorted_ = '-' + sorted_
            query = query.order_by(sorted_)
        elif sorted_ and order == 'asc':
            query = query.order_by(sorted_)

        return query

    def _yield(self, query, offset=0, limit=10, fields=None):

        # # temporary dynamic-fields for json-output
        def _jsonify_with_dynamic_fields(obj):
            _ = obj.to_json(
                follow_reference=True,
                max_depth=2
            )
            _ = json.loads(_)
            for field in self.exclude_fields:
                if field in _:
                    # current_app.logger.critical(f'deleted {field}')
                    del _[field]

            for field in self.dynamic_fields:
                if fields:
                    if field in fields:
                        _[field] = getattr(obj, field, '')
                else:
                    _[field] = getattr(obj, field, '')
            return _

        if offset:
            query = query.skip(offset)
        if limit:
            query = query.limit(limit)

        return (
            _jsonify_with_dynamic_fields(obj) for obj in query
        )


class SingleResource(Resource):
    exclude_fields = []

    def get(self, id):
        queryset = self.resource_cls.objects
        if self.exclude_fields:
            queryset = queryset.exclude(*self.exclude_fields)
        return jsonify(json.loads(queryset.get_or_404(id=id).to_json()))


class SingleListResource(ListResource):

    '''단일pk를 조회해서 목록을 조회하는 resources
    resource_cls or queryset() have to be provided.'''

    def queryset(self, pk):
        return self.resource_cls.objects(pk=pk)

    def get(self, id):
        fields = request.args.get('fields', None)  # field1,field2,field3 ..
        filter_ = request.args.get('filter', None)  # filters={"hello":"world"}
        limit = request.args.get('limit', 10, int)
        offset = request.args.get('offset', 0, int)
        order = request.args.get('order', 'asc')
        search = request.args.get('search', None)  # unified_search_text
        sorted_ = request.args.get('sort', '')  # +field1,-field2

        query = self._build_queryset(
            self.queryset(id),
            search=search,
            fields=fields,
            filter_=filter_,
            sorted_=sorted_,
            order=order,
        )
        total_count = query.count()
        headers = {
            'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())

        gen = self._yield(query, offset=offset, limit=limit, fields=fields)
        # if self.dynamic_fields:
        #     # url_for와 같은 action은 response에서 수행하면
        #     # application-context가 나간 후라서 call자체가 안된다.
        #     gen = list(gen)

        return current_app.response_class(
            stream_with_context(api_gen(
                gen,
                total=total_count,
            )),
            headers=headers,
            mimetype='application/json')

    def delete(self, id):
        deleted = 0
        failed = 0
        for obj in self.queryset(id).filter(id__in=request.json['ids']):
            try:
                obj.delete()
                deleted += 1
            except (mongoengine.OperationError, mongoengine.ValidationError):
                failed += 1

        if deleted == 0 and failed == 0:
            return jsonify(deleted=deleted, failed=failed), 404

        return jsonify(deleted=deleted, failed=failed)


class GenResource(Resource):

    '''목록의 크기를 알 수 없는 경우를 위한, generator형식으로 데이터 생성'''

    def gen(self, **kwargs):
        yield

    def get(self):
        # args
        search = request.args.get('search', '')  # unified_search_text
        limit = request.args.get('limit', 10, int)
        offset = request.args.get('offset', 0, int)

        genobj = self.gen(**dict(search=search, limit=limit, offset=offset))

        headers = {
            # 'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        # headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            stream_with_context(api_gen(genobj, **{'from': offset, 'to': offset + limit})),
            headers=headers,
            mimetype='application/json')


class SingleGenResource(GenResource):

    '''단일pk를 조회해서 목록을 조회하는 resources
    목록의 크기를 알 수 없고, generator형식으로 데이터 생성'''

    def gen(self, **kwargs):
        yield

    def get(self, id):
        # args
        search = request.args.get('search', '')  # unified_search_text
        limit = request.args.get('limit', 10, int)
        offset = request.args.get('offset', 0, int)

        genobj = self.gen(**dict(id=id, search=search, limit=limit, offset=offset))

        headers = {
            # 'X-Total-Count': total_count,
            # 'X-Total-Pages': int(total_count / page_size),
        }
        # headers.update(self.response_headers())
        headers['Access-Control-Expose-Headers'] = ','.join(headers.keys())
        return current_app.response_class(
            stream_with_context(api_gen(genobj, **{'from': offset, 'to': offset + limit})),
            headers=headers,
            mimetype='application/json')
