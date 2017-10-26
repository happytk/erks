# -*-encoding:utf-8 -*-

from bson.dbref import DBRef
from mongoengine import ValidationError, NotUniqueError

from flask_script import Manager  # , prompt_bool, prompt
from erks import db, _create_app, configure_extensions
from erks.utils import password_hash

import logging

app = _create_app()
configure_extensions(app)

# manager = Manager(usage="Perform one-time migration for changing db-schema")
manager = Manager(app, usage="Migration scripts")

@manager.command
def m001_helloworld():
    pass