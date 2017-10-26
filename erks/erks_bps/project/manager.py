# -*- encoding:utf-8 -*-
from terminaltables import AsciiTable
from flask_script import Manager, prompt_bool
from mongoengine.errors import NotUniqueError

from erks.models import (
    Project,
    ProjectGroup,
    # Order,
    # Product,
    # Coupon,
    User, ProjectUser, ProjectGroupUser, ProjectUserBase
)

manager = Manager(usage="Perform project operation")


def pay_simulation(self, user, months=3):
    coupon = Coupon(issuer=user,
                    product=Product.objects.get(product_code='project_unlimited'),
                    quantity=int(months),
                    expired_when=None,
                    group_id='manage-script-coupon').save()

    assert isinstance(self, Project)
    assert self.project_group.is_default is True

    start, end = self.calculate_subscription_period(coupon.quantity)
    Order(payer=user,
          product=coupon.product,
          quantity=coupon.quantity,
          project=self,
          started_when=start,
          expired_when=end).save()

    table_data = []
    table_data.append(['_id', 'start', 'end'])
    table_data.append([self.id, start, end])
    table = AsciiTable(table_data)
    print(table.table)


# monkey-patching pay-simulaion
Project.__pay_by_coupon = pay_simulation


@manager.command
def apply_coupon(email, project_id, months=3):
    """issue a coupon and apply to project"""
    try:
        user = User.objects.get(email=email)
    except:
        print("User({0}) doesn't exists.".format(email))
        return

    try:
        project = Project.objects.get(id=project_id)
    except:
        print("Project({0} doesn't exists.".format(project_id))
        return

    project.__pay_by_coupon(user, int(months))


@manager.command
def pg_migrate(project_id, project_group_slug):

    project_group = ProjectGroup.objects(slug=project_group_slug).first()
    project = Project.objects(id=project_id).first()
    if project_group and \
       project_group.is_not_default and \
       project and \
       prompt_bool("Are you sure you want to migrate all project-env?"):

        project.project_group = project_group
        project.save()

        # project_group_join
        for user in project.members:
            try:
                pgu = project_group.join(user)
            except NotUniqueError:
                pgu = ProjectGroupUser.objects.get(
                    project_group=project_group, user=user
                )
            # user.default_project_group_id = pg.id
            # user.save()

            # project_user
            pu = ProjectUserBase.objects.get(project=project, user=user)
            pu.project_group_user = pgu
            pu.save()

        # pg.save()
        print('done')


@manager.command
def check_integrity():
    def _assert(exp):
        if exp:
            pass
        else:
            import pdb
            pdb.set_trace()

    for project in Project.objects(project_group=ProjectGroup.default()).all():
        print('checking.. {} users'.format(project.id))

        # project must have one owner
        _assert(ProjectUser.objects(project=project, is_owner=True).count() == 1)

        # project_user - project_group_user mappring
        for pu in ProjectUser.objects(project=project):
            print('checking.. {}'.format(pu))
            _assert(pu.project_group_user.project_group == project.project_group)
            _assert(pu.project_group_user.user == pu.user)

        print('checking.. {} orders'.format(project.id))
        if project.is_free:
            _assert(project.product == Product.default())
        else:
            _assert(project.product != Product.default())
