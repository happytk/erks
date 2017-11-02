# -*- encoding:utf-8 -*-
import uuid
import datetime
from werkzeug.utils import secure_filename
import os
import json
from .models import *


class TypesystemParser:
    def __init__(self, filename, filepath, project_id):
        self.uploaded_file = os.path.join(filepath, filename)
        self.global_file_name = filename
        self.global_project_id = project_id

    global_file_name = None
    global_project_id = None

    def get_base_document(self, document_index=0, modified_date=0):
        if self.global_document_id is None:
            self.global_document_id = str(uuid.uuid1())

        document_id = str(self.global_document_id) + "-{0}".format(document_index)
        document = {"id": document_id,
                    "name": None,
                    "text": None,
                    "status": "READY",
                    "modifiedDate": modified_date}
        return document

    @classmethod
    def get_base_set(cls):
        token = {"id": None,
                 "name": None,
                 "documents": [],
                 "count": None,
                 "type": False,
                 "modifiedDate": 0}
        return token

    @classmethod
    def get_epoch_time(cls):
        epoch = datetime.datetime.utcfromtimestamp(0)
        return int((datetime.datetime.today() - epoch).total_seconds() * 1000.0)

    def wks_json_parser(self):
        print(self.uploaded_file)
        f = open(self.uploaded_file, 'r')
        data = f.read()
        f.close()

        json_data = json.loads(data)

        entity_types = json_data["entityTypes"]
        relationship_types = json_data["relationshipTypes"]
        sire_info = None
        functional_entity_types = None
        kgimported = None
        if "sireInfo" in json_data :
            sire_info = json_data["sireInfo"]
        else:
            sire_info = get_default_sire_info()
        if "functionalEntityTypes" in json_data:
            functional_entity_types = json_data["functionalEntityTypes"]
        else:
            functional_entity_types = None

        if "kgimported" in json_data:
            kgimported = json_data["kgimported"]
        else:
            kgimported = None

        self.create_entity_types(entity_types)
        self.create_relationship_types(relationship_types)
        self.create_sire_info(sire_info)

    def create_entity_types(self, entity_types):
        entity_types_collection.update(
            {"project_id": self.global_project_id},
            {
                "$set":{"entity_types": entity_types}
            },
            multi=False,
            upsert=True
        )




    def create_relationship_types(self, relationship_types):
        relationship_types_collection.update(
            {"project_id": self.global_project_id},
            {
                "$set": {"relationship_types": relationship_types}
            },
            multi=False,
            upsert=True
        )


    def create_sire_info(self, sire_info):
        sire_info_collection.update(
            {"project_id": self.global_project_id},
            {
                "$set": {"sire_info": sire_info}
            },
            multi=False,
            upsert=True
        )
