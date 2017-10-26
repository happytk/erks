# -*- encoding:utf-8 -*-
from flask import Blueprint, jsonify, request, Response, stream_with_context, current_app, url_for
from flask_login import current_user
from erks.extensions import db  # noqa
import os
import xlsxwriter

bpapp = Blueprint(
    'exporter',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static_exporter')


def _dot_getter(obj, accessor, default='-'):
    accs = accessor.split('.')
    for acc in accs:
        obj = obj.get(acc, default)
        if obj is None:
            return obj

    return obj


class TableExporter(db.DynamicDocument):
    def generate(self):
        apiobj = current_app.view_functions[self.endpoint].view_class()

        if hasattr(apiobj, 'queryset_advsearch'):
            d = {}
            d.update(self.endpoint_kwargs)
            d['args'] = self.url_params
            queryset = apiobj.queryset_advsearch(**d)
        else:
            queryset = apiobj.queryset(**self.endpoint_kwargs)

        query = apiobj._build_queryset(
            queryset,
            search=self.url_params.get('search', None),
            fields=self.url_params.get('fields', None),
            filter_=self.url_params.get('filter_', None),
            sorted_=self.url_params.get('sorted_', None),
            order=self.url_params.get('order', 'asc'),
        )
        total_count = query.count()

        fileid = str(current_user.to_dbref().id)
        filename = "{0}.xlsx".format(fileid)
        filepath = os.path.join(current_app.config['EXCEL_UPLOAD_DIR'], filename)
        # current_app.logger.debug(filepath)
        workbook = xlsxwriter.Workbook(
            filepath, {'constant_memory': True}
        )
        worksheet = workbook.add_worksheet('ERCC')
        for colidx, column in enumerate(self.columns):
            worksheet.write(0, colidx, column.get('title', 'Nonamed'))
        current_app.logger.debug(self.columns[-1])
        for index, row in enumerate(apiobj._yield(
                query,
                limit=0,
                fields=self.url_params.get('fields', None))):
            for colidx, column in enumerate(self.columns):
                try:
                    val = _dot_getter(row, column.get('field'))
                except (ValueError, AttributeError):
                    val = '-'
                else:
                    current_app.logger.debug(val)
                    worksheet.write(index + 1, colidx, val)
            yield f'data: {index+1}/{total_count}\n\n'
        workbook.close()
        url = url_for('portal.download_file', file_id=fileid)
        yield f'event: completed\ndata: <a href="{url}">엑셀파일을 다운로드받으세요.</a>\n\n'


@bpapp.route('/_exporter', methods=['POST', ])
def _exporter():
    table_exporter = TableExporter(**request.json)
    table_exporter.url_root = request.url_root
    table_exporter.save()
    return jsonify(ret=True, id=str(table_exporter.id))


@bpapp.route('/_run/<mbj:exporter_id>', methods=['GET', ])
def _run(exporter_id):
    table_exporter = TableExporter.objects.get(id=exporter_id)
    return Response(stream_with_context(table_exporter.generate()),
                    mimetype='text/event-stream')
