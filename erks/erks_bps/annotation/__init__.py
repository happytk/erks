# -*- encoding:utf-8 -*-
from flask import Blueprint

bpapp = Blueprint('annotation', __name__,
                  template_folder='templates',
                  static_folder='static',
                  static_url_path='/static_annotator'
                  )


from . import views