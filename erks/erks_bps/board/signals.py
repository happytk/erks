# -*-encoding:utf-8-*-
from copy import deepcopy
from datetime import datetime
from flask_babel import gettext
from erks.signals import on_created_project


def publish_guides(project):
    from erks.erks_bps.project.models import Project
    from erks.erks_bps.board.models import Post
    guide_project = Project.objects(title='NEXCORE ER-C 소개').first()
    if guide_project:
        guide_posts = Post.objects(project=guide_project).all()
        for post in guide_posts:
            new_post = deepcopy(post)
            new_post.id = None
            new_post.project = project
            new_post.writer = project.owner
            new_post.created_at = datetime.now()
            new_post.save(clean=False)


on_created_project.connect(publish_guides)
