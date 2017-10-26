# -*-encoding:utf-8-*-
import logging
from bson.dbref import DBRef
from xlsxwriter import Workbook
from ercc.errors import ExcelWriteDataTypeError


class TermExcelColumn(object):
    TEXT = 'TEXT'
    BOOLEAN = 'BOOLEAN'
    DATE = 'DATE'
    OBJECT = 'OBJECT'
    LIST = 'LIST'
    PHYSICAL_TERM_FULLNAME = 'PHYSICAL_TERM_FULLNAME'
    """ docstring for TermExcelColumn
        엑셀 다운로드에서 사용할 컬럼정보 클래스
        컬럼의 타입별로 MongoDB에서 조회하기 위한 정보 저장

    """
    def __init__(self, column_name, data_type, object_cls=None, field=None):
        super(TermExcelColumn, self).__init__()
        self.column_name = column_name
        self.data_type = data_type
        self.object_cls = object_cls
        self.field = field
        self.cached = {}


    """
    mongo db field type 별로 출력을 위한 function을 정의
    """

    def text(self, data):
        return str(data)

    def boolean(self, data):
        return 'Y' if data else 'N'

    def date(self, data):
        return data.strftime('%Y-%m-%d %H:%M:%S')

    def object(self, data, key=None):
        _collection = self.object_cls._get_collection()
        if isinstance(data, DBRef):
            object = _collection.find_one({'_id': data.id})
        else:
            object = _collection.find_one({'_id': data})
        return object.get(key if key else self.field, '')

    def list(self, data):
        value = list()
        for v in data:
            value.append(self.cached_data(v , 'object'))

        return "/".join(value)

    def physical_term_fullname(self, data):
        # if self.cached_data(data, 'object', key='physical_term_fullname'):
        #     return self.cached_data(data, 'object', key='physical_term_fullname')
        name = self.object(data, key='physical_term_fullname')
        # import pdb; pdb.set_trace()
        if name:
            return name

        compositions = ' '.join(self._composition_physical_full_str(data))
        compositions = compositions.split()

        def make_first_lower(x):
            return x[0].lower() + x[1:]

        if len(compositions):
            words = map(lambda x: x[0].upper() + x[1:], compositions[1:])
            return make_first_lower(compositions[0]) + ''.join(words)
        else:
            return ''

    """
    function 정의
    """

    def _composition_physical_full_str(self, data):
        return filter(
            lambda x: x,
            map(lambda x: self.physical_term_fullname(x), self._composition(data))
        )

    def _composition(self, data):
        # return self.cached_data(data, 'object', key='composition')
        return self.object(data, key='composition')


    def cached_data(self, data, func, **kwargs):
        # from flask import current_app
        if data in self.cached:
            # current_app.logger.debug(f'{data}-{func}-{kwargs}-{data in self.cached}-{self.cached}')
            return self.cached[data]
        else:
            if kwargs:
                self.cached[data] = getattr(self, func)(data, **kwargs)
            else:
                self.cached[data] = getattr(self, func)(data)

            # current_app.logger.debug(f'{data}-{func}-{kwargs}-{data in self.cached}-{self.cached[data]}')
            return self.cached[data]


class ExcelHelper(object):

    def __init__(self, filepath):
        self.filepath = filepath
        self._workbook = Workbook(filepath, {'constant_memory': True})

    def write_header(self, work_sheet, header_columns):
        for idx, column in enumerate(header_columns):
            # 컬럼 Header 셋팅
            if isinstance(header_columns[column], TermExcelColumn):
                work_sheet.write(0, idx, header_columns[column].column_name)
            else:
                work_sheet.write(0, idx, header_columns[column])

    def write_row(self, work_sheet, row_num, data, ordered_columns):
        for i, column_name in enumerate(ordered_columns):
            column = ordered_columns[column_name]
            column_value = data.get(column_name, '')

            if isinstance(column, TermExcelColumn) and column_value:
                if column.data_type == TermExcelColumn.LIST:
                    work_sheet.write(row_num, i, getattr(column, column.data_type.lower())(column_value))
                else:
                    work_sheet.write(row_num, i, column.cached_data(column_value, column.data_type.lower()))
            else:
                work_sheet.write(row_num, i, column_value)


    def write_sheet(self, ordered_columns, rows, title=None):

        work_sheet = self._workbook.add_worksheet(title)
        self.write_header(work_sheet, ordered_columns)

        for idx, data in enumerate(rows):
            row_num = idx + 1
            self.write_row(work_sheet, row_num, data, ordered_columns)

    def save(self):
        self._workbook.close()
