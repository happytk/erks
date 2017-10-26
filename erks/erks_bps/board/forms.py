# -*-encoding:utf-8-*-
from flask_mongoengine.wtf import model_form
from flask_wtf import FlaskForm as Form
from wtforms import (
    TextField,
    FileField,
)
from erks.erks_bps.board.models import Reply, Post
from erks.utils.form.widgets import SummerNoteWidget


class SearchForm(Form):
    search_text = TextField(u'search_text')


class BoardForm(model_form(
    Post,
    only=[
        'title',
        'contents',
    ],
    field_args={
        'contents': {
            'widget': SummerNoteWidget(),
        }
    }
)):
    '''board contents shouldn't be escaped.
    but default-wtforms-field does auto-escaping.'''
    tmp_file = FileField()


class ReplyForm(model_form(
    Reply,
    exclude=[
        'created_at',
    ],
)):
    pass
