# -*-encoding:utf-8-*-
from blinker import signal

# user
on_created_user = signal('on_created_user')
on_verified_user = signal('on_verified_user')

# project-group
on_created_project_group = signal('on_created_project_group')
on_changed_project_group = signal('on_changed_project_group')
on_joined_to_project_group = signal('on_joined_to_project_group')

# project
on_created_project = signal('on_created_project')
on_deleted_project = signal('on_deleted_project')
on_joined_project = signal('on_joined_project')  # 프로젝트에 사용자 가입시
on_waited_project = signal('on_waited_project')
on_invited_project = signal('on_invited_project')
on_leaved_project = signal('on_leaved_project')  # 프로젝트에서 사용자 떠날시

on_changed_project = signal('on_changed_project')
on_changed_project_owner = signal('on_changed_project_owner')
on_changed_project_modeler = signal('on_changed_project_modeler')
on_changed_project_term_manager = signal('on_changed_project_term_manager')

# board
on_created_post = signal('on_created_post')
on_deleted_post = signal('on_deleted_post')
on_replied_post = signal('on_replied_post')
on_modified_post = signal('on_modified_post')

# model
on_created_model = signal('on_created_model')
