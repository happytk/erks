# -*-encoding:utf8-*-
import json
from . import bpapp
from .models import Post, ProjectPost, ProjectGroupNotice, ProjectGroupQnA
from .forms import (
    BoardForm,
    SearchForm,
)

from erks.erks_bps.project.models import Project
from erks.erks_bps.project_group.models import ProjectGroup
from erks.utils.portlet import Portlet

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    abort,
    make_response,
    g,
    jsonify,
)
from flask_login import current_user
from flask_babel import lazy_gettext
from erks.utils import (
    flash_error,
    flash_success,
    flash_warning,
    register_breadcrumb,
    default_breadcrumb_root
)
from mongoengine import Q


default_breadcrumb_root(bpapp, '.')


@bpapp.route('/p/<mbj:project_id>/posts')
@register_breadcrumb(bpapp, '.index', lazy_gettext(u'커뮤니티'))
def posts(project_id):
    return render_template(
        'project/portlets.htm.j2',
        active_page='board',
        portlets=[
            Portlet('board._posts', project_id=project_id)
        ]
    )


@bpapp.route('/pg/<slug>/_summary_projectgroup_notice')
def _summary_projectgroup_notice(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group.has_theme():
        theme_key = project_group.theme_key
        return render_template(
            f'theme/{theme_key}/board/_summary_projectgroup_notice.htm.j2', slug=slug)
    else:
        return render_template('board/_summary_projectgroup_notice.htm.j2', slug=slug)


@bpapp.route('/pg/<slug>/_summary_projectgroup_qna')
def _summary_projectgroup_qna(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    if project_group.has_theme():
        theme_key = project_group.theme_key
        return render_template(
            f'theme/{theme_key}/board/_summary_projectgroup_qna.htm.j2', slug=slug)
    else:
        return render_template('board/_summary_projectgroup_qna.htm.j2', slug=slug)


@bpapp.route('/pg/<slug>/_notices')
def _project_group_notices(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template('board/_project_group_notices.htm.j2', slug=slug)


@bpapp.route('/pg/<slug>/_qnas')
def _project_group_qnas(slug):
    project_group = ProjectGroup.objects.get_or_404(slug=slug)
    return render_template('board/_project_group_qnas.htm.j2', slug=slug)


@bpapp.route('/p/<mbj:project_id>/_posts', methods=['GET', 'POST'])
def _posts(project_id):
    page = request.args.get('page', 0, type=int)
    edit_yn = request.args.get('edit_yn')
    search_text = request.args.get('search_text')
    per_page = 5

    q = (
        Q(project=g.project) &
        Q(use_yn=True)
    )

    if request.method == 'POST':
        form = SearchForm(request.form)
        q = q & (
            Q(title__icontains=form.search_text.data) |
            Q(contents__icontains=form.search_text.data)
        )
    else:
        form = SearchForm()
        if search_text:
            form.search_text.data = search_text
            q = q & (
                Q(title__icontains=form.search_text.data) |
                Q(contents__icontains=form.search_text.data)
            )

    if page:
        # more처리
        posts = Post.objects(q)\
            .order_by('-created_at')\
            .skip(int(page) * per_page)\
            .limit(per_page)
        return render_template(
            'board/_posts_more.html',
            posts=posts,
            project=g.project)
    elif edit_yn is not None:
        limit = (page + 1) * per_page
    else:
        limit = per_page

    posts = Post.objects(q).order_by('-created_at').limit(limit)
    is_more = (
        len(posts) % per_page == 0 and
        len(posts) != 0
    )
    can_write = current_user.is_active and \
        g.project.check_to_enter(current_user._get_current_object())
    return render_template(
        'board/_posts.html',
        form=form,
        posts=posts,
        page=page,
        is_more=is_more,
        can_write=can_write,
        project=g.project)


@bpapp.route('/p/<mbj:project_id>/_post', methods=['POST', 'GET', ])
@register_breadcrumb(bpapp, '.index.post_write', lazy_gettext(u'글쓰기'))
def _post_write(project_id):

    project = Project.objects.get_or_404(id=project_id)
    form = BoardForm(request.form)

    if request.method == 'POST' and form.validate():

        post = ProjectPost()
        post.project = project
        post.writer = current_user.to_dbref()

        form.populate_obj(post)

        # filename = form.tmp_file.name
        # filedata = request.files[filename]
        # if filedata.filename:
        #     post.file = filedata
        #     post.filename = filedata.filename  # todo: python3compatible

        post.save()
        return redirect(url_for(
            '._post_view',
            post_id=post.id))

    return render_template(
        'project/community_write.htm.j2',
        action_url=url_for('board._post_write', project_id=project_id),
        project=project, form=form)


@bpapp.route('/pg/<slug>/_notice_write', methods=['POST', 'GET', ])
def _notice_write(slug):

    pg = ProjectGroup.objects.get_or_404(slug=slug)
    form = BoardForm(request.form)

    if request.method == 'POST' and form.validate():
        post = ProjectGroupNotice()
        post.project_group = pg
        post.writer = current_user.to_dbref()

        form.populate_obj(post)
        post.save()
        return redirect(url_for(
            '._notice_view',
            post_id=post.id))

    return render_template(
        'board/_post_write.htm.j2',
        action_url=url_for('board._notice_write', slug=slug),
        form=form
    )


@bpapp.route('/b/<mbj:post_id>/_notice_view', methods=['GET', ])
def _notice_view(post_id):
    post = ProjectGroupNotice.objects.get_or_404(id=post_id)
    return render_template(
        'board/_post_view.html',
        post=post,
        board_list_url=url_for('._project_group_notices', slug=post.project_group.slug)
    )


@bpapp.route('/pg/<slug>/_qna_write', methods=['POST', 'GET', ])
def _qna_write(slug):

    pg = ProjectGroup.objects.get_or_404(slug=slug)
    form = BoardForm(request.form)

    if request.method == 'POST' and form.validate():
        post = ProjectGroupQnA()
        post.project_group = pg
        post.writer = current_user.to_dbref()

        form.populate_obj(post)
        post.save()
        return redirect(url_for(
            '._qna_view',
            post_id=post.id))

    return render_template(
        'board/_post_write.htm.j2',
        action_url=url_for('board._qna_write', slug=slug),
        form=form
    )


@bpapp.route('/b/<mbj:post_id>/_qna_view', methods=['GET', ])
def _qna_view(post_id):
    post = ProjectGroupQnA.objects.get_or_404(id=post_id)
    return render_template(
        'board/_post_view.html',
        post=post,
        board_list_url=url_for('._project_group_qnas', slug=post.project_group.slug)
    )


@bpapp.route('/b/<mbj:post_id>', methods=['POST', 'GET', ])
@register_breadcrumb(bpapp, '.index.post_view', lazy_gettext(u'게시글 상세보기'))
def post_view(post_id):
    post = Post.objects.get_or_404(id=post_id)
    if isinstance(post, ProjectPost):
        return render_template(
            'project/portlets.htm.j2',
            active_page='board',
            portlets=[
                Portlet('board._post_view', post_id=post_id),
                # Portlet('board._post_replies_view', post_id=post_id),
            ]
        )
    else:
        # projectgroup쪽은 popup으로만 보여지기 때문에
        # base_template이 없다. 404처리
        abort(404)
        # return render_template(
        #     'project/portlets.htm.j2',
        #     active_page='board',
        #     portlets=[
        #         Portlet('board._post_view', post_id=post_id),
        #         # Portlet('board._post_replies_view', post_id=post_id),
        #     ]
        # )


@bpapp.route('/b/<mbj:post_id>/_view', methods=['GET', ])
def _post_view(post_id):
    post = Post.objects.get_or_404(id=post_id)
    if isinstance(post, ProjectPost):
        return render_template(
            'project/community_view.htm.j2',
            project=g.project,
            post=post,
            board_list_url=url_for('._posts', project_id=post.project.id)
        )
    elif isinstance(post, ProjectGroupNotice):
        return render_template(
            'board/_post_view.html',
            post=post,
            board_list_url=url_for('._project_group_notices', slug=post.project_group.slug)
        )
    elif isinstance(post, ProjectGroupQnA):
        return render_template(
            'board/_post_view.html',
            post=post,
            board_list_url=url_for('._project_group_qnas', slug=post.project_group.slug)
        )
    else:
        abort(404)


@bpapp.route('/b/<mbj:post_id>/_replies', methods=['GET', ])
def _post_replies_view(post_id):
    post = Post.objects.get_or_404(id=post_id)
    replies = post.get_replies(sort=True, reverse=False)
    paging = request.args.get('paging')
    fndtext = request.args.get('fndtext')

    if isinstance(post, ProjectPost):
        can_write = current_user.is_active and \
            g.project.check_to_enter(current_user._get_current_object())
    else:
        can_write = True

    return render_template(
        'board/_post_replies_view.html',
        post=post,
        replies=replies,
        can_write=can_write,
        paging=paging,
        fndtext=fndtext)


@bpapp.route('/b/<mbj:post_id>/_del', methods=['GET', ])
def _post_delete(post_id):

    post = Post.objects.get_or_404(id=post_id)

    if not (post.writer == current_user._get_current_object()):
        flash_error(lazy_gettext(u'권한이 없습니다.'))
        return redirect(url_for('._post_view', post_id=post_id))
    else:
        post.use_yn = False
        post.save()
        flash_success(lazy_gettext(u'게시글이 삭제되었습니다'))
        if isinstance(post, ProjectPost):
            return redirect(url_for('._posts', project_id=g.project.id))
        else:
            return redirect(url_for('._notice_view', post_id=post_id))

@bpapp.route('/b/<mbj:post_id>/_edt', methods=['POST', 'GET'])
def _post_modify(post_id):

    post = Post.objects.get_or_404(id=post_id)

    if not (post.writer == current_user._get_current_object()):
        flash_error(lazy_gettext(u'권한이 없습니다.'))
        return redirect(url_for('._post_view', post_id=post_id))

    if request.method == 'POST':
        form = BoardForm(request.form)
        if form.validate():
            form.populate_obj(post)

            # filedata = request.files["tmp_file"]
            # if (filedata is not None) or \
            #         (filedata is None and post.filename != ''):
            #     post.file = filedata
            #     # .encode('utf8')  # python3compatible
            #     post.filename = filedata.filename
            post.save()
            flash_success(lazy_gettext(u'게시글이 수정되었습니다'))
            return redirect(url_for(
                '._post_view',
                post_id=post.id))
    else:
        form = BoardForm(obj=post)

    return render_template(
        'board/_post_write.htm.j2',
        action_url=url_for('board._post_modify', post_id=post_id),
        project=g.project,
        form=form)


@bpapp.route('/b/<mbj:post_id>/r_new', methods=['POST', 'GET', ])
@bpapp.route('/b/<mbj:post_id>/r/<mbj:reply_id>/edt', methods=['POST', 'GET', ])
def replysave(post_id, reply_id=None):

    post = Post.objects.get_or_404(id=post_id)

    reply_contents = request.form.get('reply')
    if not reply_id:
        if reply_contents and len(reply_contents.strip()) > 0:
            post.write_reply(
                current_user._get_current_object(),
                reply_contents)
        else:
            flash_warning(lazy_gettext(u'답글내용이 없어서 저장되지 않았습니다'))
    else:
        use_yn = request.form.get('use_yn' + str(reply_id))
        if use_yn == 'N':
            post.delete_reply(reply_id)
        else:
            if reply_contents and len(reply_contents.strip()) > 0:
                post.edit_reply(reply_id, reply_contents)
            else:
                flash_warning(lazy_gettext(u'답글내용이 없어서 저장되지 않았습니다'))
    return redirect(url_for(
        '._post_replies_view',
        post_id=post_id))


@bpapp.route('/b/<mbj:post_id>/dwn', methods=['POST', 'GET', ])
def download(post_id):
    post = Post.objects.get_or_404(id=post_id)
    try:
        file_binary = post.file.read()
        if file_binary:
            # todo: python3compatible
            filename = 'attachment; filename={0}'.format(post.filename)

            response = make_response(file_binary)
            response.headers['Content-Type'] = 'image/jpeg'
            response.headers['Content-Disposition'] = filename
            return response
        else:
            abort(404)
    except IOError:
        # image_binary = None
        abort(500)
