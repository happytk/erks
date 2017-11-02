# -*-encoding: utf-8-*-
from flask import url_for, g, current_app
from flask_wtf import FlaskForm as Form
from flask_mongoengine.wtf import model_form
from flask_login import (
    current_user,
)
from flask_babel import lazy_gettext
from datetime import datetime
from dateutil.relativedelta import relativedelta

from wtforms import (
    # Form,
    TextField,
    # SelectField,
    FileField,
    HiddenField,
    validators,
    BooleanField,
    widgets,
)
from wtforms.validators import ValidationError

# from erks.erks_bps.projectuser.models import (
#     ProjectWaitingUserOutbound, ProjectUser
# )
# from erks.erks_bps.billing.models import Product, Coupon
from erks.erks_bps.project_group.models import ProjectGroup
from erks.erks_bps.project.models import Project
# from erks.erks_bps.glossary.models import Glossary, GlossaryBase
# from erks.erks_bps.erc.models import Model
from erks.utils.form.validators import image_file_validator
from erks.utils.form.fields import ReferenceField
# from erks.erks_bps.billing.forms import (
#     KsNetBillingFormMixIn,
#     ProductBillingMixIn,
# )
from erks.models import User
from flask_babel import gettext

import json
from supports import wtformsparsleyjs

from erks.extensions import db


class DocumentUploadForm(Form):
    title = TextField('title', [validators.Length(min=2, max=255)])
    # banner_imgf = FileField(u'배너 이미지')

class DocumentSetsForm(db.Document):
    title = db.StringField(required=False, max_length=255, min_length=2)