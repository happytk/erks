# -*- encoding:utf-8 -*-
from flask import Blueprint

bpapp = Blueprint('login', __name__,
                  template_folder='templates',
                  static_folder='static')

from . import views  # noqa
from . import signals  # noqa
# from . import models


# def accept_subscribe(sender, **kw):
#     msg = u"You've accepted into %s project by %s."
#     msg = msg % (kw.get('project'), sender)
#     models.UserNotification(user=kw.get('whom'), message=msg, type=kw.get('type'), type_value=str(sender.id)).save()
# user_accept_news = signal('user_accept')
# user_accept_news.connect(accept_subscribe)


# def decline_subscribe(sender, **kw):
#     msg = u"You've declined to %s project by %s." % (kw.get('project'), sender)
#     models.UserNotification(user=kw.get('whom'), message=msg, type=kw.get('type'), type_value=str(sender.id)).save()
# user_decline_news = signal('user_decline')
# user_decline_news.connect(decline_subscribe)


# def reject_subscribe(sender, **kw):
#     msg = u"You've rejected your request to join %s project by %s."
#     msg = msg % (kw.get('project'), sender)
#     models.UserNotification(user=kw.get('whom'), message=msg, type=kw.get('type'), type_value=str(sender.id)).save()
# user_reject_news = signal('user_reject')
# user_reject_news.connect(reject_subscribe)
