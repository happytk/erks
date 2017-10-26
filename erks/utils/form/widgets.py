# -*- encoding:utf-8 -*-
import json
from wtforms.widgets import HTMLString, html_params

from flask_admin._compat import as_unicode
from flask_admin.babel import gettext
from flask_admin.helpers import get_url

from erks.utils import santinize


class DialogTableSelectWidget(object):
    '''reference_id를 hiddenfield로 갖고,
    해당 id를 찾기 위한 dialog를 띄우고 싶을때 쓰는 widget
    dialog는 별도로 작성해주어야 함.'''

    def __call__(self, field, **kwargs):
        button_text = gettext('선택하기')
        obj_id = field.data.id if field.data else ''
        obj_value = str(field.data) if field.data else ''
        return HTMLString(f'''
<div class="input-group">
    <input class="form-control"
           readonly="readonly"
           id="{field.id}_name"
           name="{field.id}_name"
           value="{obj_value}"/>
    <input type="hidden"
           name="{field.id}"
           id="{field.id}"
           value="{obj_id}"/>
    <span class="input-group-btn">
        <a class="btn btn-warning"
                id="select_{field.id}">
            <i class="fa fa-arrow-left fa-fw"/></i>
            {button_text}
        </a>
    </span>
</div>''')


class SummerNoteWidget(object):
    """summernote는 내용을 escape처리하면 안된다. santinize처리만 한다."""

    def __init__(self):
        pass

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        params = html_params(name=field.name, **kwargs)
        value = santinize(field._value())

        return HTMLString('''
<div %(params)s>%(value)s</div>
<textarea %(params)s style="display:none"></textarea>
''' % dict(params=params, value=value))


class AjaxSelect2Widget(object):  # for v4.0
    """flask_admin에서 제공하는 ajaxselect2widget 수정.
    view-url을 customized할 수 없으므로 자체구현한 것으로 대체"""

    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', 'select2-ajax')

        # field의 options로 정의된 param들을 data-url에 붙여준다.
        # 추후필요에 따라 data-url자체를 재정의할 수 있는 방법도 제공해주면 좋겠다.
        url = get_url('portal.ajax_model_lookup',
                      name=field.loader.name,
                      querym=json.dumps(field.options))
        kwargs.setdefault('data-url', url)
        # kwargs.setdefault('data-url', field.loader.data_url)

        allow_blank = getattr(field, 'allow_blank', False)
        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'hidden')

        options_string = []
        if self.multiple:
            result = []
            ids = []

            for value in field.data:
                data = field.loader.format(value)
                options_string.append(HTMLString(
                    '<option %s>%s</option>' % (html_params(value=data[0]), data[1])))
                result.append(data)
                ids.append(as_unicode(data[0]))

            separator = getattr(field, 'separator', ',')

            kwargs['value'] = separator.join(ids)
            kwargs['data-json'] = json.dumps(result)
            kwargs['data-multiple'] = u'1'
        else:
            data = field.loader.format(field.data)

            if data:
                options_string.append(HTMLString(
                    '<option %s>%s</option>' % (html_params(value=data[0]), data[1])))
                kwargs['value'] = data[0]
                kwargs['data-json'] = json.dumps(data)

        placeholder = gettext(field.loader.options.get(
            'placeholder', 'Please select model'))
        kwargs.setdefault('data-placeholder', placeholder)

        return HTMLString('<select %s>%s</select>' % (
            html_params(name=field.name, **kwargs),
            '\n'.join(options_string)))


class AjaxSelect2_v35_Widget(object):
    """flask_admin에서 제공하는 ajaxselect2widget 수정.
    view-url을 customized할 수 없으므로 자체구현한 것으로 대체"""

    def __init__(self, multiple=False):
        self.multiple = multiple

    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', 'select2-ajax')

        # field의 options로 정의된 param들을 data-url에 붙여준다.
        # 추후필요에 따라 data-url자체를 재정의할 수 있는 방법도 제공해주면 좋겠다.
        url = get_url('portal.ajax_model_lookup',
                      name=field.loader.name,
                      querym=json.dumps(field.options))
        kwargs.setdefault('data-url', url)
        # kwargs.setdefault('data-url', field.loader.data_url)

        allow_blank = getattr(field, 'allow_blank', False)
        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'

        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', 'hidden')

        if self.multiple:
            result = []
            ids = []

            for value in field.data:
                data = field.loader.format(value)
                result.append(data)
                ids.append(as_unicode(data[0]))

            separator = getattr(field, 'separator', ',')

            kwargs['value'] = separator.join(ids)
            kwargs['data-json'] = json.dumps(result)
            kwargs['data-multiple'] = u'1'
        else:
            data = field.loader.format(field.data)

            if data:
                kwargs['value'] = data[0]
                kwargs['data-json'] = json.dumps(data)

        placeholder = gettext(field.loader.options.get(
            'placeholder', 'Please select model'))
        kwargs.setdefault('data-placeholder', placeholder)

        return HTMLString('<input %s>' % html_params(
            name=field.name, **kwargs))
