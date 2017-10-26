# # -*-encoding:utf-8-*-
# from flask import current_app
# import xlsxwriter

# class Exp(object):
#     def __init__(self, filepath):
#         pass
#     def write(self, data, title=None):
#         pass
#     def close(self):
#         pass

# class XlsExp(Exp):

#     def __init__(self, filepath) :
#         self.workbook = xlsxwriter.Workbook(filepath, {'constant_memory': True})
#         self.filepath = filepath

#     def write(self, data, title):
#         pass

#     def make_work_sheet(self, column_dict, data_list, title):
#         current_app.logger.debug("make_work_sheet called")
#         work_sheet = self.workbook.add_worksheet(title)

#         for i, column_name in enumerate(column_dict):
#             work_sheet.write(0, i, unicode(column_dict[column_name]))

#         for idx, data in enumerate(data_list) :
#             row = idx + 1
#             for i, column_name in enumerate(column_dict):
#                 work_sheet.write(row , i, unicode(data[column_name]))

#     def close(self):
#         self.workbook.close()
