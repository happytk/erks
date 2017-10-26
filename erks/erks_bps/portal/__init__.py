# -*- encoding:utf-8 -*-
from flask import Blueprint  # noqa

bpapp = Blueprint('portal', __name__,
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='/static_portal')

from erks.extensions import db  # noqa

# bpapp을 loading시에 view가 같이 import되어야 route정보에 함께 등록된다.
# 그렇지않으면 별도로 view를 import해줘야 하므로 번거롭기 때문에,
# 이곳에 loading 로직을 첨부한다.
from . import views  # noqa
