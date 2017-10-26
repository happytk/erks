# -*- encoding:utf-8 -*-

from terminaltables import AsciiTable
from flask_script import Manager, prompt

from erks.erks_bps.project_group.models import ProjectGroup, ProjectGroupUser
from erks.models import (
    # Order,
    User,
    # Product, Coupon
)
from slugify import slugify
from datetime import datetime

manager = Manager(usage="Perform project_group operation")


@manager.command
def list():

    pgs = ProjectGroup.objects.all()
    table_data = []
    table_data.append(['_id', 'slug', 'is_default', 'users'])
    for pg in pgs:
        user_count = ProjectGroupUser.objects(project_group=pg).count()
        table_data.append([str(pg.id), pg.slug, str(pg.is_default), user_count])
    table = AsciiTable(table_data)
    print(table.table)


@manager.command
def create():

    project_group_name = prompt('project group name')

    while True:
        project_group_slug = prompt('project group slug', default=slugify(project_group_name.lower()))
        if ProjectGroup.objects(slug=project_group_slug).first() is None:
            break
    project_group_description = prompt('project group description', default='this is project group for \'{0}\''.format(project_group_name))
    # project_group_private = prompt_bool('is private?', default=True)
    # project_group_visible = prompt_bool('is visible?', default=True)

    while True:
        project_group_manager_email = prompt('project group manager(email)')
        manager = User.objects(email=project_group_manager_email).first()
        if manager is None:
            print('Sorry, there is no user - {0}'.format(project_group_manager_email))
        else:
            break

    pg = ProjectGroup(title=project_group_name, slug=project_group_slug, description=project_group_description).save()
    ProjectGroupUser(project_group=pg, user=manager, is_owner=True).save()
    print('created successfully.')


@manager.command
def apply_coupon(email, slug, months=3):
    """issue a coupon and apply to project_group"""

    def pay_simulation(self, user, months=3):
        coupon = Coupon(issuer=user,
                        product=Product.objects.get(product_code='group_unlimited'),
                        quantity=int(months),
                        expired_when=None,
                        group_id='manage-script-coupon').save()

        assert isinstance(self, ProjectGroup)

        start, end = self.calculate_subscription_period(coupon.quantity)
        Order(payer=user,
              product=coupon.product,
              quantity=coupon.quantity,
              project_group=self,
              started_when=start,
              expired_when=end).save()
        table_data = []
        table_data.append(['_id', 'start', 'end'])
        table_data.append([self.id, start, end])
        table = AsciiTable(table_data)
        print(table.table)

    # monkey-patching pay-simulaion
    ProjectGroup.__pay_by_coupon = pay_simulation

    try:
        user = User.objects.get(email=email)
    except:
        print("User({0}) doesn't exists.".format(email))
        return

    try:
        pg = ProjectGroup.objects.get(slug=slug)
    except:
        print("ProjectGroup({0} doesn't exists.".format(slug))
        return

    pg.__pay_by_coupon(user, int(months))


@manager.command
def check_integrity():
    def _assert(exp):
        if exp:
            pass
        else:
            import pdb
            pdb.set_trace()

    for pg in ProjectGroup.objects.all():
        print('checking.. {} users'.format(pg.slug))
        if pg == ProjectGroup.default():
            continue

        # project must have one owner
        _assert(ProjectGroupUser.objects(project_group=pg, is_owner=True).count() == 1)

        print('checking.. {} orders'.format(pg.slug))
        orders = Order.objects(project_group=pg, canceled=False, expired_when__gte=datetime.now()).all()
        if len(orders):
            for order in orders:
                if order.started_when < datetime.now() < order.expired_when:
                    break
            else:
                print('linear-history is broken')
                import pdb
                pdb.set_trace()
