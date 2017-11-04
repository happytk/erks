# -*- encoding:utf-8 -*-
import uuid
import datetime
from erks.utils.log_exception import log_exception
from werkzeug.utils import secure_filename
import os
from .models import *


class MyException(Exception):
    pass


class DocumentParser:
    def __init__(self, filename=None, filepath="/", project_id=None):
        self.uploaded_file = os.path.join(filepath, filename)
        self.global_file_name = filename
        self.global_project_id = project_id

    token_breaker = '-', ',', '.'
    token_breaker_2 = "'s", "\'s"

    sentence_breaker = '.',

    global_document_id = None
    global_modified_date = None
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
    def get_base_ground_truth(cls, document):
        ground_truth = {"id": document["id"],
                        "name": document["name"],
                        "version": 3,
                        "text": document["text"],
                        "docLength": 0,
                        "language": "EN",
                        "modifiedDate": document["modifiedDate"],
                        "documentSet": [],
                        "preannotation": [],
                        "sentences": [],
                        "mentions": [],
                        "relations": [],
                        "corefs": [],
                        "typeResolved": True,
                        "userResolved": False}
        return ground_truth

    @classmethod
    def get_base_sentence(cls):
        sentence = {"id": None,
                    "begin": 0,
                    "end": 150,
                    "text": None,
                    "tokens": []}
        return sentence

    @classmethod
    def get_base_token(cls):
        token = {"id": None,
                 "begin": 0,
                 "end": 150,
                 "text": None,
                 "whiteSpace": False}
        return token

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
        epoch = datetime.utcfromtimestamp(0)
        return int((datetime.today() - epoch).total_seconds() * 1000.0)

    def csv_parser(self):
        f = open(self.uploaded_file, 'r')
        data = f.read()
        f.close()
        """
        http://www.kimgentes.com/worshiptech-web-tools-page/2008/10/14/regex-pattern-for-parsing-csv-files-with-embedded-commas-dou.html

        ("(?:[^"]|"")*"|[^,]*)*(,("(?:[^"]|"")*"|[^,]*))
        """

        """
        for match in pattern.finditer(data):
            print match.groups()[0]
        """
        documents = self.document_parser(data)

        self.clear_project_documents(document_type="regular_sets")


        self.create_documents(documents, document_type="regular_sets")
        self.create_ground_truth(documents, document_type="regular_sets")
        self.create_sets(documents, document_type="regular_sets")

    def online_text_parser(self, text):
        text = text.replace('"', "'")
        text = '"online text","' + text + '"'
        documents = self.document_parser(text)

        self.clear_project_documents(document_type="online_text")

        self.create_documents(documents=documents, document_type="online_text")
        self.create_ground_truth(documents, document_type="online_text")
        self.create_sets(documents, document_type="online_text")

    def document_parser(self, data):

        offset = 0
        str_buffer = []
        is_name = True
        is_in_quote = False
        documents = []

        document_index = 1

        if self.global_modified_date is None:
            self.global_modified_date = self.get_epoch_time()

        tmp_document = self.get_base_document(document_index=document_index, modified_date=self.global_modified_date)

        """에라 모르겠다...정규식은 실패임"""
        try:
            length = len(data)

            iter_data = iter(data)

            for char in iter_data:

                if is_name:
                    if char == ",":
                        tmp_document["name"] = ''.join(str_buffer).strip()
                        str_buffer = []
                        is_name = False

                    else:
                        str_buffer.append(char)

                else:
                    if is_in_quote:
                        if char == '"':
                            if offset + 1 < length and data[offset + 1] == '"':
                                str_buffer.append(char)
                                # str_buffer.append(data[offset + 1])
                                #iter_data.next()
                                next(iter_data)

                            else:
                                tmp_document["text"] = ''.join(str_buffer).strip()
                                str_buffer = []
                                is_name = True
                                is_in_quote = False
                                documents.append(tmp_document)
                                document_index += 1
                                tmp_document = self.get_base_document(document_index=document_index,
                                                                      modified_date=self.global_modified_date)

                        else:
                            str_buffer.append(char)

                    else:
                        if char == '"':
                            is_in_quote = True
                        else:
                            if char == " " or char == "\t":
                                pass
                            else:
                                raise MyException("wrong document format")

                offset += 1
            # print documents

        except MyException as e:
            log_exception(e)
        except Exception as e:
            log_exception(e)

        return documents

    def clear_project_documents(self, document_type):
        documents_collection.remove(
            {
                "project_id": self.global_project_id,
                "document_type": document_type
            },
            {
                "justOne": False
            }
        )

        ground_truth_collection.remove(
            {
                "project_id": self.global_project_id,
                "document_type": document_type
            },
            {
                "justOne": False
            }
        )

        documents_sets_collection.remove(
            {
                "project_id": self.global_project_id,
                "document_type": document_type
            },
            {
                "justOne": False
            }
        )


    def create_documents(self, documents, document_type):
        documents_collection.insert_one({"project_id": self.global_project_id,
                                         "documents": documents,
                                         "document_type": document_type
                                         })
        pass

    def create_ground_truth(self, documents, document_type):
        str_buffer = []
        is_begin_set = False
        for document in documents:
            ground_truth = self.get_base_ground_truth(document)
            text = ground_truth["text"]

            offset = 0
            begin = 0
            length = len(text)
            iter_data = iter(text)
            try:
                for char in iter_data:
                    if char == "\r":
                        if offset + 1 < length and text[offset + 1] == '\r':
                            self.sentence_parser(ground_truth=ground_truth, begin=begin, sentence_buffer=str_buffer)
                            str_buffer = []
                            iter_data.next()
                            offset += 1
                            is_begin_set = False
                        else:
                            str_buffer.append(char)
                    elif char in self.sentence_breaker:
                        str_buffer.append(char)
                        self.sentence_parser(ground_truth=ground_truth, begin=begin, sentence_buffer=str_buffer)
                        str_buffer = []
                        is_begin_set = False

                    else:
                        str_buffer.append(char)
                        if not is_begin_set:
                            begin = offset
                            is_begin_set = True

                    offset += 1
                self.sentence_parser(ground_truth=ground_truth, begin=begin, sentence_buffer=str_buffer)
            except Exception as e:
                log_exception(e)


            ground_truth_collection.insert_one({"project_id": self.global_project_id,
                                                "global_document_id": self.global_document_id,
                                                "ground_truth": ground_truth,
                                                "document_type": document_type
                                                })

    def sentence_parser(self, ground_truth, begin, sentence_buffer):
        text = ''.join(sentence_buffer).rstrip()

        begin += (len(text) - len(text.lstrip()))

        text = text.lstrip()
        length = len(text)
        if length > 0:
            sentence = self.get_base_sentence()
            sentence_id = "s" + str(len(ground_truth["sentences"]))
            sentence["id"] = sentence_id
            sentence["begin"] = begin

            end = len(text.lstrip()) + begin

            sentence["end"] = end
            sentence["text"] = text

            str_buffer = []
            iter_data = iter(text)
            offset = begin
            begin = begin
            text_offset_diff = begin
            is_begin_set = False

            for char in iter_data:
                text_offset = offset - text_offset_diff
                if offset > 227:
                    pass
                if char == ' ' or char == '\t':
                    self.token_parser(sentence=sentence, sentence_id=sentence_id, begin=begin, token_buffer=str_buffer)
                    str_buffer = []
                    is_begin_set = False
                elif char in self.token_breaker:
                    self.token_parser(sentence=sentence, sentence_id=sentence_id, begin=begin, token_buffer=str_buffer)
                    str_buffer = []
                    begin = offset
                    str_buffer.append(char)
                    self.token_parser(sentence=sentence, sentence_id=sentence_id, begin=begin, token_buffer=str_buffer)
                    str_buffer = []
                    is_begin_set = False
                elif text_offset + 1 < length and char + text[text_offset+1] in self.token_breaker_2:
                    self.token_parser(sentence=sentence, sentence_id=sentence_id, begin=begin, token_buffer=str_buffer)
                    str_buffer = []
                    begin = offset
                    str_buffer.append(char)
                    str_buffer.append(text[text_offset + 1])
                    self.token_parser(sentence=sentence, sentence_id=sentence_id, begin=begin, token_buffer=str_buffer)
                    #iter_data.next()
                    next(iter_data)
                    offset += 1
                    str_buffer = []
                    is_begin_set = False
                else:
                    str_buffer.append(char)
                    if not is_begin_set:
                        begin = offset
                        is_begin_set = True

                offset += 1

            ground_truth["sentences"].append(sentence)

    def token_parser(self, sentence, sentence_id, begin, token_buffer):
        text = ''.join(token_buffer).rstrip()

        begin += len(text) - len(text.lstrip())
        text = text.lstrip()

        if len(text) > 0:
            token = self.get_base_token()
            token_id = sentence_id + "-t" + str(len(sentence["tokens"]))
            token["id"] = token_id
            token["begin"] = begin
            end = len(text.lstrip()) + begin
            token["end"] = end
            token["text"] = text
            sentence["tokens"].append(token)

    def create_sets(self, documents, document_type):
        sets = []
        document_set = self.get_base_set()
        document_set["id"] = "id-all"
        document_set["name"] = "All"
        for document in documents:
            document_set["documents"].append(document["id"])
        document_set["count"] = len(documents)
        document_set["type"] = "ALL"
        document_set["modifiedDate"] = 0
        sets.append(document_set)

        # 이부분 하드코딩임. 몇개가 들어가야할지 아직 불확실함
        # 파일 여러번 넣으면 계속 추가되는거 같음.
        document_set = self.get_base_set()
        document_set["id"] = str(self.global_document_id)
        document_set["name"] = self.global_file_name
        for document in documents:
            document_set["documents"].append(document["id"])
        document_set["count"] = len(documents)
        document_set["type"] = "SOURCE"
        document_set["modifiedDate"] = self.global_modified_date
        sets.append(document_set)

        documents_sets_collection.insert_one({"project_id": self.global_project_id,
                                    "sets": sets,
                                    "document_type": document_type,
                                    })







