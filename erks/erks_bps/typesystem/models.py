# -*- encoding:utf-8 -*-
import uuid
import datetime
#from util import *
from werkzeug.utils import secure_filename
import os
from bson import json_util

import json

from erks.extensions import db

def get_default_sire_info():
    return {
        "entityProp" : {
            "roles" : None,
            "color" : None,
            "mentionType" : [
                {
                    "color" : "white",
                    "hotkey" : "1",
                    "name" : "NAM",
                    "backGroundColor" : "#AA00FF"
                },
                {
                    "color" : "black",
                    "hotkey" : "2",
                    "name" : "NOM",
                    "backGroundColor" : "#00FF7F"
                },
                {
                    "color" : "black",
                    "hotkey" : "3",
                    "name" : "PRO",
                    "backGroundColor" : "#AAFFFF"
                },
                {
                    "color" : "white",
                    "hotkey" : "4",
                    "name" : "NONE",
                    "backGroundColor" : "gray"
                }
            ],
            "roleOnly" : False,
            "clazz" : [
                {
                    "color" : "#A5A5A5",
                    "hotkey" : "3",
                    "name" : "SPC",
                    "backGroundColor" : "white"
                },
                {
                    "color" : "black",
                    "hotkey" : "2",
                    "name" : "NEG",
                    "backGroundColor" : "#00FF7F"
                },
                {
                    "color" : "black",
                    "hotkey" : "1",
                    "name" : "GEN",
                    "backGroundColor" : "#AAFFFF"
                }
            ],
            "active" : True,
            "backGroundColor" : None,
            "hotkey" : None,
            "subtypes" : None
        },
        "relationProp" : {
            "color" : None,
            "clazz" : [
                {
                    "name" : "SPECIFIC"
                },
                {
                    "name" : "NEG"
                },
                {
                    "name" : "OTHER"
                }
            ],
            "active" : True,
            "tense" : [
                {
                    "name" : "PAST"
                },
                {
                    "name" : "PRESENT"
                },
                {
                    "name" : "FUTURE"
                },
                {
                    "name" : "UNSPECIFIED"
                }
            ],
            "backGroundColor" : None,
            "hotkey" : None,
            "modality" : [
                {
                    "name" : "ASSERTED"
                },
                {
                    "name" : "OTHER"
                }
            ]
        }
    }


class EntityTypes(db.DynamicDocument):
    meta = {'collection': 'entity_types'}


class LogicalEntityTypes(db.DynamicDocument):
    meta = {'collection': 'logical_entity_types'}


class RelationshipTypes(db.DynamicDocument):
    meta = {'collection': 'relationship_types'}


class LogicalRelationshipTypes(db.DynamicDocument):
    meta = {'collection': 'logical_relationship_types'}


class TypeSystemDiagram(db.DynamicDocument):
    meta = {'collection': 'type_system_diagram'}


class SireInfo(db.DynamicDocument):
    meta = {'collection': 'sire_info'}

entity_types_collection = EntityTypes._get_collection()
logical_entity_types_collection = LogicalEntityTypes._get_collection()
relationship_types_collection = RelationshipTypes._get_collection()
logical_relationship_types_collection = LogicalRelationshipTypes._get_collection()
type_system_diagram_collection = TypeSystemDiagram._get_collection()
sire_info_collection = SireInfo._get_collection()

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
    relationship_type_types = relationship_types_collection.find_one({"project_id": project_id})
    logical_relationship_types = logical_relationship_types_collection.find_one({"project_id": project_id})
    if logical_relationship_types is not None:
        logical_relationship_type_map = {}

        for logical_relationship_type in logical_relationship_types["logical_relationship_types"]:
            logical_relationship_type_map[logical_relationship_type["label"]] = logical_relationship_type["logical_value"]["ko"]
        for relationship_type in relationship_type_types["relationship_types"]:
            if relationship_type["label"] in logical_relationship_type_map:
                relationship_type["logical_value"] = logical_relationship_type_map[relationship_type["label"]]
    return relationship_type_types["relationship_types"]


def get_type_system_diagram(project_id):
    diagram = type_system_diagram_collection.find_one({"project_id": project_id})

    return diagram["type_system_diagram"] if diagram is not None else None

def get_typesystem(project_id):
    entity_types = entity_types_collection.find_one({"project_id": project_id})
    relationship_types = relationship_types_collection.find_one({"project_id": project_id})
    typesystem = {"entityTypes": entity_types["entity_types"],
                  "relationshipTypes": relationship_types["relationship_types"]
                  }
    return typesystem

def save_all_typesystem(project_id, type_system_diagram, entity_types, relation_types):
    new_entity_types = []
    new_logical_entity_types = []
    new_relation_types = []
    new_logical_relation_types = []

    for key, entity_type in entity_types.items():
        #logical_entity_type.setdefault(key, []).append(value)
        new_logical_entity_type = {}
        logical_value = entity_type["logical_value"] if "logical_value" in entity_type else None
        definition = entity_type["definition"] if "definition" in entity_type else None
        if logical_value is not None or definition is not None:
            new_logical_entity_type["label"] = entity_type["label"]
            if definition is not None:
                new_logical_entity_type["definition"] = definition
            if logical_value is not None:
                new_logical_entity_type["logical_value"] = {"ko": logical_value}
            new_logical_entity_types.append(new_logical_entity_type)


        entity_type.pop('logical_value', None)
        entity_type.pop('definition', None)
        new_entity_types.append(entity_type)

    for key, relation_type in relation_types.items():
        new_logical_relation_type = {}
        logical_value = relation_type["logical_value"] if "logical_value" in relation_type else None
        definition = relation_type["definition"] if "definition" in relation_type else None
        if logical_value is not None or definition is not None:
            new_logical_relation_type["label"] = relation_type["label"]
            if definition is not None:
                new_logical_relation_type["definition"] = definition
            if logical_value is not None:
                new_logical_relation_type["logical_value"] = {"ko": logical_value}
                new_logical_relation_types.append(new_logical_relation_type)

        relation_type.pop('logical_value', None)
        relation_type.pop('definition', None)
        new_relation_types.append(relation_type)

    logical_entity_types_collection.update(
        {
            "project_id": project_id,
        },
        {
            "$set": {"logical_entity_types": new_logical_entity_types}
        },
        multi=False,
        upsert=True
    )

    entity_types_collection.update(
        {"project_id": project_id,
        },
        {
            "$set": {"entity_types": new_entity_types}
        },
        multi=False,
        upsert=True
    )

    logical_relationship_types_collection.update(
        {
            "project_id": project_id,
        },
        {
            "$set": {"logical_relationship_types": new_logical_relation_types}
        },
        multi=False,
        upsert=True
    )

    relationship_types_collection.update(
        {"project_id": project_id,
        },
        {
            "$set": {"relationship_types": new_relation_types}
        },
        multi=False,
        upsert=True
    )

    result = type_system_diagram_collection.update(
        {"project_id": project_id,
        },
        {
            "$set": {"type_system_diagram": type_system_diagram}
        },
        multi=False,
        upsert=True
    )

    return result
