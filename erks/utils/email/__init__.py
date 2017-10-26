# -*-encoding:utf-8-*-
from erks.extensions import db, mail
from flask import current_app
from flask_mail import Message
import logging as logger


class EMail(db.Document):
    """
    email이 거쳐가는 임시 repo로 사용.
    필요시 재전송이 가능하도록
    """

    title = db.StringField(required=True, max_length=200)
    body = db.StringField(required=True, max_length=4000)
    sender = db.EmailField(required=True)
    receiver = db.EmailField(required=True)

    def send(self):
        msg = Message(self.title, sender=self.sender, recipients=[self.receiver])
        msg.body = self.body
        # msg.html = messsage
        mail.send(msg)


def sendmail(receiver, title, body):
    sender = current_app.config['DEFAULT_SITE_EMAIL_ADDR']
    try:
        e = EMail(title=title, body=body, receiver=receiver, sender=sender)
        if current_app.config['EMAIL_SENT_ARCHIVE']:
            e.save()
        e.send()
        return True
    except Exception as e:
        logger.critical('email sending error', exc_info=True)
        return False
