# -*-encoding:utf8 -*-
from bson import ObjectId
import json
from collections import Counter
from erks.utils.portlet import Portlet

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    abort,
    g,
    current_app,
    jsonify,
    send_file,
)
from flask_login import current_user
from flask_babel import lazy_gettext, gettext

from erks.utils import (
    flash_error,
    flash_success,
    flash_warning,
    flash_info,
    register_breadcrumb,
    default_breadcrumb_root
)
from erks.erks_bps.login.models import User
# from erks.erks_bps.billing.models import Order, Coupon
# from erks.erks_bps.projectuser.models import (
#     ProjectUserBase,
#     ProjectUser,
# )
from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser
from erks.erks_bps.project.models import (
    Project,
    ProjectSummary,
    # ProjectNotification,
)
from . import bpapp
from mongoengine import ValidationError
from werkzeug.utils import secure_filename
import os
from .models import *
from .document_parser import DocumentParser
from .document_exporter import export_document_sets
from .forms import DocumentSetsForm, DocumentUploadForm
from bson.json_util import dumps

default_breadcrumb_root(bpapp, '.')

@bpapp.route('/<project_id>/documentsList', methods=['GET', 'POST'])
def documents_list(project_id='asdf'):
    # form = RegistrationForm.objects.get_or_404(id='test')

    form = DocumentUploadForm((request.form))

    # basedoc =  baseDocument.objects.get_or_404(title="asdf")
    basedoc = DocumentSetsForm()
    basedoc.project_id = project_id

    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = current_app.config['UPLOAD_DIR']
        file.save(os.path.join(current_app.config['UPLOAD_DIR'], filename))

        form.populate_obj(basedoc)

        #basedoc.save()

        parser = DocumentParser(filename=filename, filepath=filepath, project_id=project_id)
        parser.csv_parser()

        # return render_template('documents.html.tmpl', active_menu="documents", form=form, document_sets=document_sets)

    else:
        pass

    project_sets = documents_sets_collection.find_one({"project_id": project_id, "document_type": "regular_sets"})
    document_sets = project_sets["sets"] if project_sets is not None else []

    return render_template('documents.htm.j2', active_menu="documents", form=form, document_sets=document_sets)


@bpapp.route('/<project_id>/documents/export', methods=['GET', 'POST'])
def documents_export(project_id):
    zip_file_path = export_document_sets(project_id)
    return send_file(zip_file_path, mimetype='application/octet-stream')


@bpapp.route('/<project_id>/documents/onlineTextParser', methods=['GET', 'POST'])
def online_text_parser(project_id):
    text = str(request.json['text'])
    result = {}
    parser = DocumentParser(filename="online_text", filepath="/", project_id=project_id)
    parser.online_text_parser(text)
    return dumps(result, ensure_ascii=False)