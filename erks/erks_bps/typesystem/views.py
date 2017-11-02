# -*- encoding:utf-8 -*-
from flask import render_template, request, redirect, url_for, Response, current_app
from . import bpapp
#from runme import app
#import runme
from werkzeug.utils import secure_filename
import os
from . import typesystem_parser
from . import models
from erks.utils.log_exception import log_exception
from bson.json_util import dumps


@bpapp.route('/<projectid>/typesystemlist', methods=['GET', 'POST'])
@bpapp.route('/typesystemlist', methods=['GET', 'POST'])
def list_typesystem(projectid='asdf'):

    return render_template('typesystem.html.tmpl', projectid="asdf", active_menu="typeSystem")


@bpapp.route('/<projectid>/import', methods=['GET', 'POST'])
@bpapp.route('/import', methods=['GET', 'POST'])
def import_typesystem(projectid='asdf'):
    if request.method == 'POST':
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = current_app.config['UPLOAD_DIR']
        file.save(os.path.join(current_app.config['UPLOAD_DIR'], filename))
        parser = typesystem_parser.TypesystemParser(filename=filename, filepath=filepath, project_id=projectid)
        parser.wks_json_parser()
    return redirect(url_for('typesystem.list_typesystem'))


@bpapp.route('/getEntityTypeList/<project_id>', methods=['POST', 'GET'])
def get_entity_type_list(project_id):
    result = {}
    entity_type_list = None

    try:
        #project_id = str(request.json['project_id'])
        result = {}
        entity_type_list = models.get_entity_type_list(project_id)
        result["resultOK"] = True
        result["list"] = entity_type_list

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)


@bpapp.route('/getRelationshipTypeList/<project_id>', methods=['POST', 'GET'])
def get_relationship_type_list(project_id):
    result = {}
    relationship_type_list = None

    try:
        result = {}
        relationship_type_list = models.get_relationship_type_list(project_id)
        result["resultOK"] = True
        result["list"] = relationship_type_list

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)


@bpapp.route('/getTypeSystemDiagram/<project_id>', methods=['POST', 'GET'])
def get_type_system_diagram(project_id):
    result = {}
    try:
        type_system_diagram = models.get_type_system_diagram(project_id)
        result["resultOK"] = True
        result["result"] = type_system_diagram
    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)


@bpapp.route('/saveAll/<project_id>', methods=['POST', 'GET'])
def save_all(project_id):
    result = {}

    try:
        type_system_diagram = request.json['typeSystemDiagram']
        entity_types = request.json['entityTypes']
        relation_types = request.json['relationTypes']

        save_result = models.save_all(project_id=project_id, type_system_diagram=type_system_diagram, entity_types=entity_types, relation_types=relation_types)
        result["resultOK"] = True
        result["result"] = save_result

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)


@bpapp.route('/entityTypeDtl/<project_id>', methods=['POST', 'GET'])
def entity_type_detail(project_id):
    return render_template('entity_type_dtl.html.tmpl')


@bpapp.route('/relationTypeDtl/<project_id>', methods=['POST', 'GET'])
def relation_type_detail(project_id):
    return render_template('relation_type_dtl.html.tmpl')


@bpapp.route('/<projectid>/export', methods=['GET', 'POST'])
@bpapp.route('/export', methods=['GET', 'POST'])
def export_typesystem(projectid='asdf'):
    results = dumps(models.get_typesystem(projectid), ensure_ascii=False)
    generator = (cell for row in results for cell in row)
    return Response(generator,
                       mimetype="text/plain",
                       headers={"Content-Disposition":
                                    "attachment;filename=typesystem.json"})