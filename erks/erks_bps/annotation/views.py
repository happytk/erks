# -*- encoding:utf-8 -*-
from flask import render_template, request, send_file
from . import bpapp
#from .models import *
from erks.erks_bps.annotation import models
import json
from bson.json_util import dumps
import sys
from erks.utils.log_exception import log_exception



@bpapp.route('/<project_id>/annotationMain', methods=['GET', 'POST'])
def annotation_main(project_id):

    return render_template('annotation.html.tmpl', project_id=project_id, active_menu="humanAnnotation")


@bpapp.route('/<project_id>/annotationList', methods=['GET', 'POST'])
def annotation_list(project_id):
    annotation_list = models.get_annotation_list(project_id=project_id)
    return render_template('annotation_list.html.tmpl', project_id=project_id, active_menu="annotation", annotation_list=annotation_list)


@bpapp.route('/<project_id>/annotationTool/<document_id>', methods=['GET', 'POST'])
def annotation_tool(document_id, project_id):

    return render_template('annotation_tool.html.tmpl', project_id=project_id, document_id=document_id)


@bpapp.route('/<project_id>/mlAnnotator', methods=['GET', 'POST'])
def ml_annotator(project_id):

    return render_template('ml_annotator.html.tmpl', project_id=project_id)


@bpapp.route('/getEntityTypeList/<project_id>', methods=['POST', 'GET'])
def entity_type_list(project_id):
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


@bpapp.route('/<project_id>/getRelationshipTypeList', methods=['POST', 'GET'])
def relationship_type_list(project_id):
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

@bpapp.route('/<project_id>/getGroundTruth', methods=['POST', 'GET'])
def ground_truth(project_id):
    result = {}

    try:
        document_id = str(request.json['document_id'])
        result = {}
        document = models.get_ground_truth(project_id, document_id)
        result["resultOK"] = True
        result["document"] = document

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)

@bpapp.route('/<project_id>/getOnlineTextGroundTruth', methods=['POST', 'GET'])
def online_text_ground_truth(project_id):
    result = {}

    try:
        result = {}
        document = models.get_online_text_ground_truth(project_id)
        result["resultOK"] = True
        result["document"] = document

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)

@bpapp.route('/<project_id>/getSireInfo', methods=['POST', 'GET'])
def sire_info(project_id):
    result = {}

    try:
        document_id = str(request.json['document_id'])
        result = {}
        document = models.get_sire_info(project_id)
        result["resultOK"] = True
        result["sireInfo"] = document

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)

@bpapp.route('/<project_id>/saveAllAnnotation', methods=['POST', 'GET'])
def save_all_annotation(project_id):
    result = {}

    try:
        ground_truth_id = str(request.json['ground_truth_id'])
        save_data = request.json['saveData']
        result = {}
        save_result = models.save_all_annotation(project_id, ground_truth_id=ground_truth_id, save_data=save_data)
        result["resultOK"] = True
        result["result"] = save_result

    except Exception as e:
        result["resultOK"] = False
        result["message"] = str(Exception)
        log_exception(e)

    return dumps(result, ensure_ascii=False)


@bpapp.route('/<project_id>/runNeuroner', methods=['POST', 'GET'])
def run_neuroner(project_id):
    result = {}
    document = request.json['text']

    import run_neuroner_predict
    brat_entities = run_neuroner_predict.run_neuroner_predict_erks(project_id=project_id, document=document)
    print(brat_entitiesZ)
    result["entities"] = brat_entities

    return dumps(result, ensure_ascii=False)


