# -*-encoding:utf-8-*-
from . import bpapp
from .models import UserToken, User, PasswordVerifyToken
from .forms import LoginForm, SignUpForm, ProfileEditForm, ChangePasswordForm
from flask import (
    request,
    render_template,
    redirect,
    flash,
    url_for,
    make_response,
    current_app,
    Markup,
    session,
    g,
)
from flask_login import login_user, logout_user, current_user
from flask_babel import lazy_gettext, gettext
from mongoengine import NotUniqueError, ValidationError
from erks.utils import redirect_back, get_redirect_target, password_hash, flash_success
from erks.utils.portlet import Portlet
from erks.erks_bps.project_group.models import ProjectGroup
from erks.extensions import db

@bpapp.route('/profile')
@bpapp.route('/pg/<slug>/profile')
def profile(slug='default'):
    return render_template(
        'portlets.htm.j2',
        portlets=[
            Portlet('login._profile', slug=slug),
            Portlet('login._report_subscription', slug=slug),
        ]
    )


@bpapp.route('/_report_subscription', methods=['GET', 'POST'])
@bpapp.route('/pg/<slug>/_report_subscription', methods=['GET', 'POST'])
def _report_subscription(slug='default'):
    # pgu = current_user.queryset_project_group_user(project_group=g.project_group).first()
    project_user_objs = list(
        current_user.queryset_project_user_report_subscription
    )

    if request.method == 'POST':
        '''on처리한 project-user데이터만 들어온다.
        전부 끄고, 데이터기준으로 on한다.'''
        for subscription in project_user_objs:
            wanted = request.form.getlist(str(subscription.id))
            subscription.subscribed_report_model_glossary = 'model_glossary' in wanted
            subscription.subscribed_report_model_schema = 'model_schema' in wanted
            subscription.subscribed_report_model_change = 'model_change' in wanted
            # current_app.logger.debug(f'{subscription.subscribed_report_model_glossary}')
            if any([
                    subscription.subscribed_report_model_glossary,
                    subscription.subscribed_report_model_schema,
                    subscription.subscribed_report_model_change]):
                subscription.save()
            elif subscription.id:
                subscription.delete()
        flash_success(gettext('정상적으로 처리되었습니다.'))

        # reload (삭제된것은 지우기)
        project_user_objs = list(
            current_user.queryset_project_user_report_subscription
        )

    return render_template(
        '_report_subscription.htm.j2',
        project_user_objs=project_user_objs,
        slug=slug,
    )


@bpapp.route('/_profile')
@bpapp.route('/pg/<slug>/_profile')
def _profile(slug='default'):
    return render_template('login/_profile.html')


@bpapp.route('/profile/_password', methods=['GET', 'POST'])
def _change_password():
    user = current_user
    form = ChangePasswordForm(request.form, obj=user)
    if request.method == 'POST' and form.validate():
        # 현재사용자에 대한 비밀번호 검증
        try:
            password_identical_check = User.objects.get(
                email=user.email, password=password_hash(form.current_password.data))
        except User.DoesNotExist:
            password_identical_check = None

        if not password_identical_check:
            flash(lazy_gettext(u'입력하신 비밀번호가 현재 비밀번호와 일치하지 않습니다.'))
            # flash('The password you typed here does not match the password we currently have on file for you.')
        else:
            form.populate_obj(user)
            user.password = password_hash(user.password)
            try:
                user.save()
                flash(lazy_gettext(u'비밀번호가 변경되었습니다.'))
            except Exception:
                flash(lazy_gettext(u'문제가 발생했습니다.'))
            else:
                # internal-re-loggin
                login_user(user, remember=False)
                return redirect(url_for('login._profile'))

    return render_template('login/_change_password.htm.j2', form=form)


@bpapp.route('/profile/_edit', methods=['GET', 'POST'])
def _profile_edit():
    from erks.erks_bps.project.models import ProjectGroup
    user = current_user._get_current_object()
    form = ProfileEditForm(request.form, obj=user)

    # choices = [('', 'default'), ]
    # choices.extend([(str(g.id), g.title) for g in ProjectGroup.my()])
    choices = [(str(g.id), g.title) for g in ProjectGroup.my()]
    form.default_project_group_id.choices = choices

    if request.method == 'POST':
        if form.validate():
            form.populate_obj(user)
            user.save()
            flash_success(lazy_gettext(u'사용자 정보가 변경되었습니다.'))
            return redirect(url_for('login._profile'))
        else:
            current_app.logger.warning(form.errors)

    return render_template('login/_profile_edit.htm.j2', form=form)


def _profile_img(mailaddr, thumbnail=False):
    if mailaddr is None:
        user = current_user
    else:
        try:
            user = User.objects.get(email=mailaddr)
        except User.DoesNotExist:
            user = None

    try:
        if thumbnail and user.profile_imgf and user.profile_imgf.thumbnail:
            image_binary = user.profile_imgf.thumbnail.read()
        elif user.profile_imgf:
            image_binary = user.profile_imgf.read()
        else:
            image_binary = None
    except IOError:
        image_binary = None

    if image_binary:
        response = make_response(image_binary)
        response.headers['Content-Type'] = 'image/jpeg'
        response.headers['Content-Disposition'] = 'attachment; filename=profile.%s.jpg' % (mailaddr or '')
        return response
    else:
        if thumbnail:
            return redirect(url_for('static', filename='img/profile_thumbnail.jpg'))
        else:
            return redirect(url_for('static', filename='img/profile.png'))


@bpapp.route('/profile.timg')
@bpapp.route('/profile.<mailaddr>.timg')
def profile_timg(mailaddr=None):
    return _profile_img(mailaddr, thumbnail=True)


@bpapp.route('/profile.img')
@bpapp.route('/profile.<mailaddr>.img')
def profile_img(mailaddr=None):
    return _profile_img(mailaddr, thumbnail=False)


@bpapp.route('/profile.img/delete')
def delete_profile_img():
    if current_user.profile_imgf:
        current_user.profile_imgf.delete()
        current_user.profile_imgf = None
        current_user.save()
    return redirect(request.args.get('next') or
                    request.referrer or
                    url_for('portal.index'))


@bpapp.route('/_dev_ops_login', methods=['POST'])
def dev_ops_login():
    try:
        from Crypto.Cipher import AES
        from binascii import hexlify, unhexlify
        cobj = AES.new('erksflask!@12345', AES.MODE_ECB, 'erksflask!@12345')

        def _encrypt(text):
            pad_cnt = len(text) + 16 - (len(text) % 16)
            return hexlify(cobj.encrypt(text.ljust(pad_cnt))).decode('utf8')

        def _decrypt(text):
            return cobj.decrypt(unhexlify(text)).decode('utf8').strip()

        email = _decrypt(request.form.get("enc_email", ""))
        project_id = _decrypt(request.form.get("enc_project_id", ""))

        user = User.objects.get(email=email)
        if user.verified:
            login_user(user, remember=False)

        from erks.erks_bps.project.models import Project
        project = Project.objects.get(id=project_id)

        return redirect(url_for("project.index", project_id=project.id))

    except Exception:
        # logger.debug("Exception Occured")
        return redirect(url_for("portal.index"))


@bpapp.route('/login', methods=['GET', 'POST'])
def login():
    next_url = get_redirect_target()
    form = LoginForm(request.form)
    if request.method == 'POST':
        # import pdb; pdb.set_trace()
        if form.validate():
            try:
                email_or_userid = form.email.data
                password = form.password.data
                password = password_hash(password)
                if '@' in email_or_userid:
                    user = User.objects.get(email=email_or_userid, password=password)
                else:
                    user = User.objects.get(user_id=email_or_userid, password=password)
                if user.verified:
                    login_user(user, remember=form.remember_me.data)
                    session['lang_code'] = user.locale
                    return redirect(url_for('portal.index'))
                    # return redirect_back('portal.index')
                else:
                    message = Markup(lazy_gettext(u'이메일 인증이 완료되지 않은 사용자입니다.<br/><a href=\'#\' style=\"color: blue;\">인증 요청</a>'))
                    flash(message)
                    # flash(lazy_gettext(u'이메일 인증이 완료되지 않은 사용자입니다.'))
            except User.DoesNotExist:
                flash(lazy_gettext(u'죄송합니다. 사용자가 존재하지 않거나 비밀번호가 일치하지 않습니다.'))
        else:
            flash(lazy_gettext(u'form검증이 실패했습니다.'))
            current_app.logger.debug(form.errors)

    project_group = ProjectGroup.default()
    if project_group and project_group.has_theme():
        return render_template('theme/{theme_key}/login/login_{theme_key}.html'.format(theme_key=project_group.theme_key), form=form)
    else:
        return render_template('login/login.htm.j2', form=form, next=next_url)

    # return render_template(form.theme_page('login/login'), form=form, next=next_url)


@bpapp.route('/logout/')
def logout():
    dbname = current_app.config['SESSION_MONGODB_DB']
    collname = current_app.config['SESSION_MONGODB_COLLECT']
    db.connection[dbname][collname].delete_many(
        dict(id=f'session:{session.sid}')
    )
    logout_user()
    return redirect(url_for('portal.index'))


@bpapp.route('/signup', methods=['GET', 'POST'])
def signup():
    next_url = get_redirect_target()
    form = SignUpForm(request.form)
    if request.method == 'POST' and form.validate():
        # import pdb; pdb.set_trace()
        try:
            email = form.email.data
            password = password_hash(form.password.data)

            user = User(email=email, password=password).save()
        except NotUniqueError:
            flash(u'이미 등록된 사용자입니다.')
        except ValidationError:
            flash(u'email형식이 바르지 않습니다.')  # form에서 거르지 못하는 email형식이 있음.
        else:
            if current_app.config['EMAIL_USER_VERIFICATION']:
                token = UserToken(email=email)
                token.save()
                token.sendmail()
                return redirect(url_for('.verify_guide', email=email))
            else:
                user.verify()
                login_user(user, remember=True)
                return redirect_back('portal.index')
    else:
        current_app.logger.critical(form.errors)

    return render_template('login/signup.htm.j2', form=form, next=next_url)


@bpapp.route('/resend_verifying_mail', methods=['GET', 'POST'])
def resend_verifying_mail():
    email = request.form.get('email', None)
    if email and request.method == 'POST':
        try:
            user = User.objects.get(email=email)
            if user.verified:
                flash(lazy_gettext(u'인증된 회원 이메일 주소입니다.'))
                # return render_template('login/login.html', form=form)
                return redirect(url_for('.login'))
            user.resend_verifying_mail()
            # flash(lazy_gettext(u'인증 메일이 발송되었습니다.'))
            # flash('Password-reset-link is sent to %s' % email)
            return redirect(url_for('.verify_guide', email=email))
        except User.DoesNotExist:
            flash(lazy_gettext(u'사용자가 존재하지 않습니다.'))
            return redirect(url_for('.login'))
    else:
        # flash('Invalid Email address.')
        return redirect(url_for('.login'))


@bpapp.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    email = request.form.get('email', None)
    if email and request.method == 'POST':
        try:
            User.objects.get(email=email)
            token = PasswordVerifyToken(email=email)
            token.save()
            token.sendmail()
            flash(lazy_gettext(u'비밀번호 초기화 링크가 %(email)s 주소로 발송되었습니다.', email=email))
            # flash('Password-reset-link is sent to %s' % email)
            return redirect(url_for('portal.index'))
        except User.DoesNotExist:
            flash(lazy_gettext(u'사용자가 존재하지 않습니다.'))
            return render_template('login/forget_password.htm.j2')
    else:
        # flash('Invalid Email address.')
        return render_template('login/forget_password.htm.j2')


@bpapp.route('/verify_guide/<email>')
def verify_guide(email):
    if True:
        user = User.objects.get(email=email)
        user.verify()
    return render_template('login/verify_guide.htm.j2', email=email)


@bpapp.route('/verify/<token>', methods=['GET', ])
def verify(token):
    from datetime import datetime, timedelta

    time_threshold = datetime.now() - timedelta(days=3)

    try:
        token = UserToken.objects.get(token=token)
        if token.created_at < time_threshold:
            # User.objects(verified=False, email=token.email).delete()
            # token.delete()
            raise UserToken.DoesNotExist
        if not token.is_newest():
            raise UserToken.DoesNotExist
    except UserToken.DoesNotExist:
        flash(lazy_gettext(u'죄송합니다. 가입정보를 확인할 수 없습니다.'))
        return redirect(url_for('portal.index'))

    email = token.email
    try:
        user = User.objects.get(email=email)
        user.verify()
    except User.DoesNotExist:
        flash(lazy_gettext(u'죄송합니다. 사용자정보가 존재하지 않습니다.'))
        user = None

    token.delete()

    if user:
        # todo: 비밀번호 없이 들어왔기 때문에 로그인하지 않는 정책으로 변경할 필요가있다.
        # login_user(user)
        flash(lazy_gettext(u'거의 다 되었습니다. 로그인하시면 ER-C를 사용하실 수 있습니다.'))

    return redirect(url_for('portal.index'))


@bpapp.route('/password_verify/<token>', methods=['GET', 'POST'])
def password_verify(token):

    from datetime import datetime, timedelta
    time_threshold = datetime.now() - timedelta(hours=1)

    try:
        password_token = PasswordVerifyToken.objects.get(token=token,
                                                         created_at__gte=time_threshold)
    except PasswordVerifyToken.DoesNotExist:
        flash('Invalid token')
        return redirect(url_for('portal.index'))

    if request.method == 'POST':
        p1 = request.form['password']
        p2 = request.form['password_confirm']
        if p1 != p2:
            flash(lazy_gettext(u'비밀번호가 일치하지 않습니다.'))
            return render_template('login/verify_password.htm.j2', token=token)
        else:
            try:
                user = User.objects.get(email=password_token.email)
            except User.DoesNotExist:
                flash(lazy_gettext(u'사용자 정보가 유효하지 않습니다.'))
                return redirect(url_for('portal.index'))

            user.password = password_hash(p1)  # change to new password
            user.verified = True
            user.save()
            password_token.delete()
            login_user(user)
            flash(lazy_gettext(u'비밀번호가 변경되었습니다.'))
            return redirect(url_for('portal.index'))
    else:
        # raise token
        return render_template('login/verify_password.htm.j2', token=token)
