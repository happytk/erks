from terminaltables import AsciiTable
from flask_script import Manager
from erks.utils import password_hash
from erks.erks_bps.login.models import User

manager = Manager(usage="Perform user operation")


@manager.command
def list(email_partial=None):
    if email_partial:
        users = User.objects(email__contains=email_partial).all()
    else:
        users = User.objects.all()
    table_data = []
    table_data.append(['_id', 'email', 'verified', 'password', 'created_at'])
    for user in users:
        table_data.append([str(user.id), user.email, user.verified, user.password, str(user.created_at)])
    table = AsciiTable(table_data)
    print(table.table)


@manager.command
def verify(email):
    try:
        user = User.objects.get(email=email)
    except:
        print("User({0}) doesn't exists.".format(email))
    else:
        if user.verified:
            print("User({0} is already verified.".format(email))
        else:
            user.verify()
            print('%s user is verified.' % email)


@manager.command
def reset_password(email, new_password):
    try:
        user = User.objects.get(email=email)
    except:
        print("User({0}) doesn't exists.".format(email))
    else:
        user.verified = True
        user.password = password_hash(new_password)
        user.save()
        print('done.')


@manager.command
def make_admin(email):
    try:
        user = User.objects.get(email=email)
    except:
        print("User({0}) doesn't exists.".format(email))
    else:
        user.admin = True
        user.save()
        print('done.')


@manager.command
def create(email, password):
    try:
        user = User.objects.get(email=email)
    except:
        user = User(email=email, password=password).save()
        print('created.')
        verify(email)
    else:
        print("User({0}) already exists.".format(email))
