# -*-encoding:utf-8-*-
from six.moves.urllib.parse import urlparse, urljoin
from flask import (
    request,
    url_for,
    redirect,
    flash,
    session
)
from flask_babel import lazy_gettext
from datetime import datetime, timedelta
from jinja2 import evalcontextfilter, Markup, escape as jescape
from xml.sax.saxutils import escape, unescape

import time
import random
import re
import hashlib
import bleach
import humanize
import logging as logger
import os

from flask_breadcrumbs import (  # noqa
    register_breadcrumb,
    default_breadcrumb_root,
)

from erks.utils.models import (  # noqa
    current_user_or_none,
    ArchivableDocument,
    JsonTransferableMixin,
    JsonifyPatchMixin,
    ReferenceValidatorMixin,
    AuditableMixin,
)


def check_time(func):
    def new_func(*args, **kwargs):
        start_t = time.time()
        result = func(*args, **kwargs)
        logger.warning('function {0}, {1} elapsed.'.format(
            func.__name__, (time.time() - start_t)))
        return result
    return new_func


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


# https://wiki.python.org/moin/EscapingHtml
# escape() and unescape() takes care of &, < and >.
html_escape_table = {
    '"': "&quot;",
    "'": "&apos;"
}
html_unescape_table = {v: k for k, v in html_escape_table.items()}


def html_escape(text):
    return escape(text, html_escape_table)


def html_unescape(text):
    return unescape(text, html_unescape_table)


def flash_error(message):
    return flash(message, category='danger')


def flash_warning(message):
    return flash(message, category='warning')


def flash_success(message):
    return flash(message, category='success')


def flash_info(message):
    return flash(message, category='info')


allowed_tags = [
    'a', 'abbr', 'acronym', 'b', 'bdo', 'big', 'blockquote', 'br',
    'center', 'cite', 'code',
    'dd', 'del', 'dfn', 'div', 'dl', 'dt', 'em', 'embed', 'font',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'ins',
    'kbd', 'li', 'object', 'ol', 'param', 'pre', 'p', 'q',
    's', 'samp', 'small', 'span', 'strike', 'strong', 'sub', 'sup',
    'table', 'tbody', 'td', 'th', 'thead', 'tr', 'tt', 'ul', 'u',
    'var', 'wbr',
]
disallowed_tags_save_content = set((
    'blink', 'body', 'html',
))
allowed_styles = ['width']
allowed_attributes = [
    'align', 'alt', 'border', 'cite', 'class', 'dir',
    'height', 'href', 'src', 'style', 'title', 'type', 'width',
    'face', 'size',  # font tags
    'flashvars',  # Not sure about flashvars - if any harm can come from it
    'classid',  # FF needs the classid on object tags for flash
    'name', 'value', 'quality', 'data', 'scale',  # for flash embed param tags, could limit to just param if this is harmful
    'salign', 'align', 'wmode',
]  # Bad attributes: 'allowscriptaccess', 'xmlns', 'target'
normalized_tag_replacements = {'b': 'strong', 'i': 'em'}


def santinize(text):
    return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, styles=allowed_styles, protocols=['data'])


@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                          for p in _paragraph_re.split(jescape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target


def redirect_back(endpoint, **values):
    target = request.form['next']
    if target and is_safe_url(target):
        pass
    else:
        # not (target == url_for('portal.default_project_group_index')):  # hack: default_project_group을 파악할 수 있도록
        target = url_for(endpoint, **values)
    return redirect(target)


# helpers

def humanize_currency(v):
    humanize.i18n.activate('ko_kr')

    try:
        v = int(v)
    except (TypeError, ValueError):
        return v

    return humanize.intcomma(v)


def humanize_datetime(o, string_format=None, short=False):
    humanize.i18n.activate('ko_kr')

    if o is None:
        return ''

    if string_format:
        try:
            o = datetime.strptime(o, string_format)
        except:
            raise 'error-dt-format'
    try:
        delta = (datetime.now() - o)
        if delta < timedelta(days=1):
            ret = humanize.naturaltime(o)
        elif delta < timedelta(days=31):
            ret = lazy_gettext(u'%(days)d일 전', days=delta.days)
        elif delta < timedelta(days=365):
            # ret = o.strftime('%m월%d일')
            ret = lazy_gettext(u'%(months)d달 전', months=(delta.days / 30))
        else:
            # ret = humanize.naturalday(o, format='%Y년%m월%d일')
            # ret = o.strftime('%Y년%m월%d일')
            ret = lazy_gettext(u'%(years)d년 전', years=(delta.days / 365))

        if short:
            ret = ret.replace(' seconds ', 's ')
            ret = ret.replace(' minutes ', 'm ')
            ret = ret.replace(' hours ', 'h ')
            ret = ret.replace('an hour ', '1h ')
            ret = ret.replace('a minute ', '1m ')
        return ret  # .decode('utf-8')
        # return ret
    except Exception as e:
        # return 'error-humanized-day'
        return str(e)


def random_hello(b):
    helloes = [u'nǐ hǎo', u'hello', u'goedendag', u'bonjour',
               u'salut', u'ciào', u'hola', u'Privet!', u'shalom']
    return random.choice(helloes).title()


TAG_RE = re.compile(r'<[^>]+>')


def strip_tags(contents, strip_size):
    x = TAG_RE.sub('', contents)
    return x[:strip_size]


def humanize_binsize(num, suffix='Bytes'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


# class ArgSpecCopyDecorator(object):

#     def __getattribute__(self, name):
#         if name == '__class__':
#             # calling type(decorator()) will return <type 'function'>
#             # this is used to trick the inspect module >:)
#             return types.FunctionType
#         return super(decorator, self).__getattribute__(name)

#     def __init__(self, fn):
#         # let's pretend for just a second that this class
#         # is actually a function. Explicity copying the attributes
#         # allows for stacked decorators.
#         self.__call__ = fn.__call__
#         self.__closure__ = fn.__closure__
#         self.__code__ = fn.__code__
#         self.__doc__ = fn.__doc__
#         self.__name__ = fn.__name__
#         self.__defaults__ = fn.__defaults__
#         self.func_defaults = fn.func_defaults
#         self.func_closure = fn.func_closure
#         self.func_code = fn.func_code
#         self.func_dict = fn.func_dict
#         self.func_doc = fn.func_doc
#         self.func_globals = fn.func_globals
#         self.func_name = fn.func_name
#         # any attributes that need to be added should be added
#         # *after* converting the class to a function
#         self.args = None
#         self.kwargs = None
#         self.result = None
#         self.function = fn

#     def __call__(self, *args, **kwargs):
#         self.args = args
#         self.kwargs = kwargs

#         self.before_call()
#         self.result = self.function(*args, **kwargs)
#         self.after_call()

#         return self.result

#     def before_call(self):
#         pass

#     def after_call(self):
#         pass


def password_hash(pwd):
    return hashlib.md5(pwd.encode('utf8')).hexdigest()


def localized_img_path(img_path):
    filename, file_extension = os.path.splitext(img_path)
    return filename + "_" + session.get('lang_code', 'ko') + file_extension