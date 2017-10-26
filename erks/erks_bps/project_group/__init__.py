# -*- encoding:utf-8 -*-
from flask import Blueprint

bpapp = Blueprint('project_group', __name__, template_folder='templates', static_folder='static', static_url_path='/static_project_group')

from . import views  # noqa
from .views import preference  # noqa
from . import signals  # noqa
