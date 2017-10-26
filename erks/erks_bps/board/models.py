from . import db
from erks.utils import JsonifyPatchMixin, AuditableMixin
from erks.signals import (
    on_created_post,
    on_modified_post,
    on_replied_post,
    on_deleted_post,
)
from erks.erks_bps.login.models import User
from erks.erks_bps.project.models import Project
from erks.erks_bps.project_group.models import ProjectGroup
from erks.utils import strip_tags, santinize
from datetime import datetime, timedelta
from bson import ObjectId

import mongoengine


class Reply(db.EmbeddedDocument):
    # reply_id = db.StringField(max_length=255, required=True)
    reply_id = db.ObjectIdField(default=ObjectId)
    writer = db.ReferenceField(User, required=True)
    contents = db.StringField(required=True)
    created_at = db.DateTimeField(default=datetime.now, required=True)
    use_yn = db.BooleanField(default=True, required=True)


class PostReplyMixin(object):

    replies = db.ListField(db.EmbeddedDocumentField(Reply))

    def get_replies(self, sort=True, reverse=True):
        # exclude delete replies
        replies = list(filter(lambda x: x.use_yn, self.replies))

        if sort:
            replies.sort(key=lambda b: b.created_at, reverse=reverse)
        return replies

    def write_reply(self, writer, contents):

        contents = santinize(contents)
        new_reply = Reply(writer=writer, contents=contents)
        self.replies.append(new_reply)
        self.save()

        on_replied_post.send(self)
        return new_reply.reply_id

    def delete_reply(self, reply_id):
        target_lst = list(
            filter(lambda x: str(x.reply_id) == str(reply_id), self.replies))
        if len(target_lst):
            target_reply = target_lst[0]
            target_reply.use_yn = False
            self.save()

    def edit_reply(self, reply_id, contents):
        target_lst = list(
            filter(lambda x: str(x.reply_id) == str(reply_id), self.replies))
        if len(target_lst):

            contents = santinize(contents)

            target_reply = target_lst[0]
            target_reply.contents = contents
            self.save()


class Post(JsonifyPatchMixin, AuditableMixin, PostReplyMixin, db.Document):
    meta = {
        # 'abstract': True,
        'allow_inheritance': True,
        'ordering': ['-created_at', ]
    }
    writer = db.ReferenceField(User, required=True)
    title = db.StringField(max_length=255, required=True)
    contents = db.StringField(required=True)
    summary = db.StringField(max_length=255)
    use_yn = db.BooleanField(default=True, required=True)
    filename = db.StringField()
    file = db.FileField()
    created_at = db.DateTimeField(default=datetime.now, required=True)

    def clean(self):
        self.contents = santinize(self.contents)
        self.summary = strip_tags(self.contents, 100)

    def is_new(self, delta=timedelta(days=1)):
        return (datetime.now() - self.created_at) <= delta

    def save(self, *args, **kwargs):
        if self.id:
            on_modified_post.send(self)
        else:
            on_created_post.send(self)
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.id:
            on_deleted_post.send(self)
        return super().delete(*args, **kwargs)


class ProjectPost(Post):
    meta = {
        'indexes': [
            {'fields': ['project', 'use_yn'], },
        ],
        'ordering': ['-created_at', ]
    }

    project = db.ReferenceField(
        Project, required=True, reverse_delete_rule=mongoengine.CASCADE)


class ProjectGroupPostMixin(object):
    project_group = db.ReferenceField(
        ProjectGroup,required=True, reverse_delete_rule=mongoengine.CASCADE)


class ProjectGroupNotice(Post,
                         ProjectGroupPostMixin):
    meta = {
        'indexes': [
            {'fields': ['project_group', 'use_yn'], },
        ],
    }


class ProjectGroupQnA(Post,
                      ProjectGroupPostMixin):
    meta = {
        'indexes': [
            {'fields': ['project_group', 'use_yn'], },
        ],
    }
