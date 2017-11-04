# -*- encoding:utf-8 -*-
import uuid
import datetime
from erks.utils.log_exception import log_exception
from werkzeug.utils import secure_filename
import os
from bson import json_util
from erks.erks_bps.documents.models import *
from erks.erks_bps.typesystem.models import *

import json



def get_annotation_list(project_id):
    documents = documents_collection.find_one({
        "project_id": project_id,
        "document_type": "regular_sets",
    })
    return documents["documents"]


def get_entity_type_list(project_id):
    entity_types = entity_types_collection.find_one({"project_id": project_id})
    logical_entity_types = logical_entity_types_collection.find_one({"project_id": project_id})
    if logical_entity_types is not None:
        logical_entity_type_map = {}

        for logical_entity_type in logical_entity_types["logical_entity_types"]:
            logical_entity_type_map[logical_entity_type["label"]] = logical_entity_type
        for entity_type in entity_types["entity_types"]:
            if entity_type["label"] in logical_entity_type_map:
                logical_entity_type = logical_entity_type_map[entity_type["label"]]

                if "definition" in logical_entity_type:
                    entity_type["definition"] = logical_entity_type["definition"]
                if "logical_value" in logical_entity_type:
                    entity_type["logical_value"] = logical_entity_type["logical_value"]["ko"]
    return entity_types["entity_types"]


def get_relationship_type_list(project_id):
    entity_types = relationship_types_collection.find_one({"project_id": project_id})
    logical_relationship_types = logical_relationship_types_collection.find_one({"project_id": project_id})
    if logical_relationship_types is not None:
        logical_relationship_type_map = {}

        for logical_relationship_type in logical_relationship_types["logical_relationship_types"]:
            logical_relationship_type_map[logical_relationship_type["label"]] = logical_relationship_type["logical_value"]["ko"]
        for relationship_type in entity_types["relationship_types"]:
            if relationship_type["label"] in logical_relationship_type_map:
                relationship_type["logical_value"] = logical_relationship_type_map[relationship_type["label"]]
    return entity_types["relationship_types"]


def get_sire_info(project_id):
    sire_info = sire_info_collection.find_one({"project_id": project_id})
    return sire_info["sire_info"]


def get_ground_truth(project_id, ground_truth_id):
    document = ground_truth_collection.find_one(
        {"project_id": project_id,
         "ground_truth.id": ground_truth_id,
         "document_type": "regular_sets",
         }
    )
    return document["ground_truth"]

def get_online_text_ground_truth(project_id):
    document = ground_truth_collection.find_one(
        {"project_id": project_id,
         "document_type": "online_text",
         }
    )
    return document["ground_truth"]

def save_all_annotation(project_id, ground_truth_id, save_data):

    result = ground_truth_collection.update(
        {"project_id": project_id,
         "ground_truth.id": ground_truth_id
        },
        {
            "$set": {"ground_truth.mentions": save_data["mentions"],
                     "ground_truth.relations": save_data["relations"],
                     "ground_truth.corefs": save_data["corefs"]
                     }
        },
        multi=False,
        upsert=True
    )

    return result

