# -*-encoding:utf-8-*-
from wtforms.validators import InputRequired, Optional
from wtforms.validators import ValidationError
from PIL import Image
from flask import (
    request,
    current_app,
)


class RequiredIf(object):
    """Validates field conditionally.
    Usage::
        login_method = StringField('', [AnyOf(['email', 'facebook'])])
        email = StringField('', [RequiredIf(login_method='email')])
        password = StringField('', [RequiredIf(login_method='email')])
        facebook_token = StringField('', [RequiredIf(login_method='facebook')])
    """
    def __init__(self, *args, **kwargs):
        self.conditions = kwargs
        if len(args):
            self.message = args[0]
        else:
            self.message = 'This field is required.'

    def __call__(self, form, field):
        for name, data in self.conditions.items():
            if name not in form._fields:
                Optional(form, field)
            else:
                condition_field = form._fields.get(name)
                if condition_field.data == data and not field.data:
                    InputRequired(self.message)(form, field)
        Optional()(form, field)

required_if = RequiredIf


def image_file_validator(file_max_size_config_key):
    def _image_file_validator(form, field):
        field.data = None
        if len(request.files) > 0 and \
                field.name in request.files and \
                request.files[field.name]:
            def _get_size(fobj):
                if fobj.content_length:
                    # content_length는 올때도 있고 오지 않을때도 있다.
                    return fobj.content_length

                try:
                    pos = fobj.tell()
                    fobj.seek(0, 2)  # seek to end
                    size = fobj.tell()
                    fobj.seek(pos)  # back to original position
                    return size
                except (AttributeError, IOError):
                    pass

                # in-memory file object that doesn't support seeking or tell
                return 0  # assume small enough

            file_max_size = current_app.config[file_max_size_config_key]
            img_data_f = request.files[field.name]
            if _get_size(img_data_f) > file_max_size:
                raise ValidationError(u'이미지 파일의 크기가 너무 큽니다.')
            else:
                try:
                    Image.open(img_data_f)
                    field.data = img_data_f
                except IOError:
                    raise ValidationError(u'유효하지 않은, 혹은 처리할 수 없는 이미지 파일입니다.')

    return _image_file_validator
