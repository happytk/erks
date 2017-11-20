"""
<주의>
이곳의 설정은 변경하면 변경할때마다 형상관리에 반영되니까
이곳은 기본값을 관리하고 개인설정은 config_local.py에 합니다.

config_local.py를 만든 후 변경이 필요한 항목만 정의하면 됩니다.


변수가 정의되고 overwrite되는 순서에 유의하세요.
예) config_local로 인해서 B의 값을 30으로 예상할수도 있겠지만 B는 여전히 10입니다.

--config.py
A = 1
B = A * 10

--config_local.py
A = 3

"""

import os

_base_dir = os.environ.get('ERCC_HOME', os.environ.get('HOME', '/erks'))

DATASET = None
TOKEN_TO_VECTOR = None

"""
DEBUG는 기본적으로 RELOADER를 함께 구동하며,
LOGGING이 DEBUG로 고정됩니다.
"""
DEBUG = True


# https://stackoverflow.com/questions/14853694/python-jsonify-dictionary-in-utf-8
JSON_AS_ASCII = False


"""
LOGGING
"""
LOG_DIR = os.path.join(_base_dir, 'log')
LOG_LEVEL = 'INFO'
TRANSACTION_LOG_DIR = os.path.join(_base_dir, 'log_transaction')


# default-slug의 projectgroup은
# 개인별 상품구매, 프로젝트 생성제한 등이 고유 동작을 하는
# 대상이다. site설치등을 위해 별개의 projectgroup을 생성하고자 한다면
# 이 값을 변경한다.
DEFAULT_PROJECT_GROUP_SLUG = 'default'
# DEFAULT_PROJECT_GROUP_THEME_KEY = 'skb'


"""
layout
"""
CONTINAER_CLS = ''  # container

"""
시스템에서 발송하는 email주소 기본값
"""
DEFAULT_SITE_EMAIL_ADDR = 'do-not-reply@ercc.sk.com'

"""
관리자 이메일. semi-colon으로 구분합니다.
(복수계정에 발송하고자 할때 메일서버 설정에 따라 다를 수 있음)
"""
SITE_ADMIN_EMAIL_ADDR = ''

"""
flask-mail extension의 설정값을 따릅니다.
MAIL_SERVER = 'smtp.gmail.com'
"""
MAIL_SERVER = None
MAIL_PORT = 465
MAIL_USERNAME = 'ercCloudDev@gmail.com'
MAIL_PASSWORD = ''
MAIL_USE_TLS = False
MAIL_USE_SSL = True

"""
이메일 발송을 위한 worker가 구동되어 있을 경우 True로 설정합니다.
"""
MAIL_SENT_ASYNC = False

"""
EMAIL발송내역을 별도 db-collection에 저장합니다.
"""
EMAIL_SENT_ARCHIVE = False

"""
사용자 email승인여부를 설정합니다. False일 경우 인증과정 없이 바로 가입됩니다.
"""
EMAIL_USER_VERIFICATION = True

"""
application의 CRITICAL-ERROR를 이메일로 수신합니다.
SITE_ADMIN_EMAIL_ADDR 설정값의 이메일로 발송합니다.
MAIL_SERVER가 설정되어 있어야 합니다.
"""
EMAIL_USE_ERROR_LOGGING = False

"""
flask-mail에서 참고하는 설정값이며
TRUE일 경우 메일이 발송되지 않습니다.
"""
MAIL_SUPPRESS_SEND = True

"""
ON-PREMISES의 경우 결제모듈을 사용하지 않음
"""
BILLING = True
BILLING_KSNET_STORE_ID = '2999199999'
BILLING_PAY_METHOD_CHOICES = [
    ('1000000000', u'신용카드'),
    # ("0100000000", u'가상계좌'),
    # ("0010000000", u'계좌이체'),
    # ("0001000000", u'월드패스카드'),
    # ("0000100000", u'문화상품권'),
    # ("0000010000", u'휴대폰결제'),
    # ("0000001000", u'게임문화상품권'),
]

"""
무료프로젝트에서 기본적으로 사용하는 상품코드
"""
DEFAULT_PRODUCT_CODE_FOR_FREE_PROJECT = 'project_default'

"""
별도의 프로젝트그룹이 아닌 기본프로젝트 그룹이 가지는 상품속성
"""
DEFAULT_PRODUCT_CODE_FOR_PROJECT_GROUP = 'default'


"""
MongoDB Staging정보. 아래 형식으로 지정합니다.
DB는 mongodb의 database이름.

{'DB': "ercc", 'host': 'localhost'}
"""
MONGODB_SETTINGS = {'DB': "erks", 'host': 'localhost'}

"""
backend configuration
"""
# CELERY_USE = True
CELERY_BACKEND = 'amqp://guest:guest@localhost:5672//'
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
# CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_PERIODIC_TASK_TIME_DELTA = 60
# v4
CELERY_TASK_ALWAYS_EAGER = False
CELERY_RESULT_BACKEND = CELERY_BACKEND  # 'cache'
CELERY_CACHE_BACKEND = CELERY_BACKEND  # 'memory'
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BEAT_SCHEDULE = {
    'beat-every-5-seconds': {
        'task': 'ercc.tasks.worker_beat',
        'schedule': 5.0,
    }
}


"""
LOGIN-SECURITY
"""
SECRET_KEY = "Kee9 Th1s S3cr3t!@!"

"""
BRAND-IMAGE-SIZE
"""
PROJECT_BRAND_IMAGE_SIZE = (600, 600)
PROJECT_BRAND_IMAGE_THUMBNAIL_SIZE = (140, 140)
PROJECT_BRAND_IMAGE_MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2M
PROJECT_GROUP_BRAND_IMAGE_MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 2M
PROJECT_GROUP_BANNER_IMAGE_MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 2M

USER_PROFILE_IMAGE_MAX_CONTENT_LENGTH = PROJECT_BRAND_IMAGE_MAX_CONTENT_LENGTH

"""
ERD-FILE-UPLOAD-TEMP
"""
MAX_ERD_CONTENT_LENGTH = 100 * 1024 * 1024
ERD_UPLOAD_DIR = os.path.join(_base_dir, 'upload_files', 'erd_files')


"""
FILE-UPLOAD
아래 MAX_CONTENT_LENGTH를 넘어가면 flask에서 413에러를 발생시킨다.
이 외에도 nginx 설정이 우선할 수 있다.(client_max_body_size)
"""
MAX_CONTENT_LENGTH = max(PROJECT_BRAND_IMAGE_MAX_CONTENT_LENGTH, MAX_ERD_CONTENT_LENGTH)
UPLOAD_DIR = os.path.join(_base_dir, 'upload_files')
DOWNLOAD_DIR = os.path.join(_base_dir, 'download_files')



"""
OSS 고지문 파일 경로
"""

OSS_NOTICE_FILE_PATH = 'resources/OSS_Notice_ER-CC-20160704.pdf'


"""
Excel File Generating Folder
"""
EXCEL_UPLOAD_DIR = os.path.join(UPLOAD_DIR, 'excels')


"""
ERD 업로드용 Excel 템플릿 파일
"""
ERD_EXCEL_TEMPLATE_FILE_PATH   = 'resources/xlstmpl/UPLOAD_ERD.xlsx'
TEMPLATE_GP_INFOTYPE_FILE_PATH = 'resources/xlstmpl/gp/TEMPLATE_GP_INFOTYPE.xlsx'
TEMPLATE_GP_UNITTERM_FILE_PATH = 'resources/xlstmpl/gp/TEMPLATE_GP_UNITTERM.xlsx'
TEMPLATE_GP_STRDTERM_FILE_PATH = 'resources/xlstmpl/gp/TEMPLATE_GP_STRDTERM.xlsx'
TEMPLATE_GP_CODETERM_FILE_PATH = 'resources/xlstmpl/gp/TEMPLATE_GP_CODETERM.xlsx'
TEMPLATE_GM_INFOTYPE_FILE_PATH = 'resources/xlstmpl/gm/TEMPLATE_GM_INFOTYPE.xlsx'
TEMPLATE_GM_UNITTERM_FILE_PATH = 'resources/xlstmpl/gm/TEMPLATE_GM_UNITTERM.xlsx'
TEMPLATE_GM_STRDTERM_FILE_PATH = 'resources/xlstmpl/gm/TEMPLATE_GM_STRDTERM.xlsx'
TEMPLATE_GM_CODETERM_FILE_PATH = 'resources/xlstmpl/gm/TEMPLATE_GM_CODETERM.xlsx'
TEMPLATE_GD_CODETERM_FILE_PATH = 'resources/xlstmpl/gd/TEMPLATE_GD_CODETERM.xlsx'
TEMPLATE_GD_NONSTRDTERM_MAP_FILE_PATH = 'resources/xlstmpl/gd/TEMPLATE_GD_NONSTRDTERM_MAP.xlsx'


"""
"""
WTF_CSRF_ENABLED = False

"""
SENTRY Configuration
"""
SENTRY_USE = False
SENTRY_DSN = 'https://***@sentry.io/93685'
SENTRY_USER_ATTRS = ['email', 'name']


EVENT_170322_COUPON_ID = None


SESSION_TYPE = 'mongodb'
SESSION_MONGODB_DB = 'erks_session'
SESSION_MONGODB_COLLECT = 'sessions'

try:
    from config_local import *  # noqa: F401,F403
except ImportError:
    # no local config found
    pass
