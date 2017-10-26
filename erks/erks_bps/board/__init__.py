# -*- encoding:utf-8 -*-
from flask import Blueprint

bpapp = Blueprint('board', __name__,
                  template_folder='templates')

from erks.extensions import db
from . import views
from . import models
from . import signals