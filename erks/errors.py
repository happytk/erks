from flask_babel import lazy_gettext


class ExcelWriteDataTypeError(Exception):
    pass


class ExcelParserValidationError(Exception):
    pass


class DocumentNoChangeError(Exception):
    def __init__(self, message=lazy_gettext('변경내역이없습니다.')):
        super().__init__(message)


class ProjectGroupIntegrityError(Exception):
    pass


class AlreadyClonedCodeSetError(Exception):
    """두 개의 int 값을 입력받아 다양한 연산을 할 수 있도록 하는 클래스.

    :param int a: a 값
    :param int b: b 값
    """
    pass


class TermTypeInconsistencyError(Exception):
    pass


class InvalidUploadFileTypeError(Exception):
    pass


#
# glossary
#
class GlossaryMasterIntegrityError(Exception):
    '''glossary-master의 내부 데이터 불일치시에'''
    pass


class NoCodeSetError(Exception):
    '''codeset을 찾을 수 없을때'''
    pass


class AlreadyCreatedCodeSetError(Exception):
    '''이미 존재하는 codeset을 create할 때'''
    pass


class RootCodeSetDeleteError(Exception):
    '''root codeset을 삭제하려고 할때'''
    pass


class MasterTermRequestIntegrityError(Exception):
    pass
