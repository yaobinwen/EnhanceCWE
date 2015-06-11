from django.core.exceptions import ValidationError
from django.db import models
from cwe.models import CWE
from base.models import BaseModel
from django.db import IntegrityError
from django.utils.encoding import force_text
from django.utils.translation import ugettext as _
from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch import receiver

STATUS = [('draft', 'Draft'), ('in_review', 'In Review'), ('approved', 'Approved'), ('rejected', 'Rejected')]


class Tag(BaseModel):
    name = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        default_permissions = ('add', 'change', 'delete', 'view')

    def __unicode__(self):
        return self.name


class MisuseCase(BaseModel):
    name = models.CharField(max_length=16, null=True, blank=True, db_index=True, default="/")
    description = models.TextField()
    cwes = models.ManyToManyField(CWE, related_name='misuse_cases')
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        verbose_name = "Misuse Case"
        verbose_name_plural = "Misuse Cases"

    def __unicode__(self):
        return "%s - %s..." % (self.name, self.description[:70])


@receiver(post_save, sender=MisuseCase, dispatch_uid='misusecase_post_save_signal')
def post_save_misusecase(sender, instance, created, using, **kwargs):
    """ Set the value of the field 'name' after creating the object """
    if created:
        instance.name = "MU/{0:05d}".format(instance.id)
        instance.save()


@receiver(pre_delete, sender=MisuseCase, dispatch_uid='misusecase_delete_signal')
def pre_delete_misusecase(sender, instance, using, **kwargs):
    """
    Prevent Misuse Case deletion if use cases or muo containers are referring to it
    """
    if instance.usecase_set.exists() or instance.muocontainer_set.exists():
        raise IntegrityError(
            _('The %(name)s "%(obj)s" cannot be deleted as there are use cases or muo containers referring to it!') % {
                'name': force_text(instance._meta.verbose_name),
                'obj': force_text(instance.name),
            })


class MUOContainer(BaseModel):
    name = models.CharField(max_length=16, null=True, blank=True, db_index=True, default="/")
    cwes = models.ManyToManyField(CWE, related_name='muo_container')
    misuse_case = models.ForeignKey(MisuseCase)
    new_misuse_case = models.TextField(null=True, blank=True)
    status = models.CharField(choices=STATUS, max_length=64, default='draft')

    class Meta:
        verbose_name = "MUO Container"
        verbose_name_plural = "MUO Containers"
        # additional permissions
        permissions = (
            ('can_approve', 'Can approve MUO container'),
            ('can_reject', 'Can reject MUO container'),
            ('can_view_all', 'Can view all MUO container'),
        )

    def __unicode__(self):
        return self.name

    def action_approve(self):
        # This method change the status of the MUOContainer object to 'approved' and it creates the
        # relationship between the misuse case and all the use cases of the muo container.This change
        # is allowed only if the current status is 'in_review'. If the current status is not
        # 'in_review', it raises the ValueError with appropriate message.
        if self.status == 'in_review':
            # Create the relationship between the misuse case of the muo container with all the
            # use cases of the container
            for usecase in self.usecase_set.all():
                usecase.misuse_case = self.misuse_case
                usecase.save()

            self.status = 'approved'
            self.save()
        else:
            raise ValueError("In order to approve an MUO, it should be in 'in-review' state")

    def action_reject(self):
        # This method change the status of the MUOContainer object to 'rejected' and the removes
        # the relationship between all the use cases of the muo container and the misuse case.
        # This change is allowed only if the current status is 'in_review' or 'approved'.
        # If the current status is not 'in-review' or 'approved', it raises the ValueError
        # with appropriate message.
        if self.status == 'in_review' or self.status == 'approved':
            # Remove the relationship between the misuse case of the muo container with all the
            # use cases of the container
            # usecases = self.usecase_set.filter(misuse_case=self.misuse_case)
            for usecase in self.usecase_set.all():
                usecase.misuse_case = None
                usecase.save()

            self.status = 'rejected'
            self.save()
        else:
            raise ValueError("In order to approve an MUO, it should be in 'in-review' state")

    def action_submit(self):
        # This method change the status of the MUOContainer object to 'in_review'. This change
        # is allowed only if the current status is 'draft'. If the current status is not
        # 'draft', it raises the ValueError with appropriate message.
        if self.status == 'draft':
            self.status = 'in_review'
            self.save()
        else:
            raise ValueError("You can only submit MUO for review if it is 'draft' state")

    def action_save_in_draft(self):
        # This method change the status of the MUOContainer object to 'draft'. This change
        # is allowed only if the current status is 'rejected' or 'in_review'. If the current
        # status is not 'rejected' or 'in_review', it raises the ValueError with
        # appropriate message.
        if self.status == 'rejected' or self.status == 'in_review':
            self.status = 'draft'
            self.save()
        else:
            raise ValueError("MUO can only be moved back to draft state if it is either rejected or 'in-review' state")


@receiver(post_save, sender=MUOContainer, dispatch_uid='muo_container_post_save_signal')
def post_save_muo_container(sender, instance, created, using, **kwargs):
    """ Set the value of the field 'name' after creating the object """
    if created:
        instance.name = "MUO/{0:05d}".format(instance.id)
        instance.save()



# TODO: This method is commented now because we need to take care of multiple deletion cases once the muo container is implemented
# @receiver(pre_delete, sender=MUOContainer, dispatch_uid='muo_container_delete_signal')
# def pre_delete_muo_container(sender, instance, using, **kwargs):
#     """
#     Pre-delete checks for MUO container
#     """
#     if instance.status not in ('draft', 'rejected'):
#         raise ValidationError(_('The %(name)s "%(obj)s" can only be deleted if in draft of rejected state') % {
#                                     'name': force_text(instance._meta.verbose_name),
#                                     'obj': force_text(instance.name),
#                                 })
#     elif instance.usecase_set.count() == 1:
#         # what if this muo container contains more than 1 use case?
#         instance.usecase_set.delete()
#     else:
#         raise ValidationError(_('The %(name)s "%(obj)s" can only be deleted because there are other use cases referring to it!') % {
#                                     'name': force_text(instance._meta.verbose_name),
#                                     'obj': force_text(instance.name),
#                                 })


class UseCase(BaseModel):
    name = models.CharField(max_length=16, null=True, blank=True, db_index=True, default="/")
    description = models.TextField()
    osr = models.TextField()
    misuse_case = models.ForeignKey(MisuseCase, null=True, blank=True)
    muo_container = models.ForeignKey(MUOContainer)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        verbose_name = "Use Case"
        verbose_name_plural = "Use Cases"

    def __unicode__(self):
        return "%s - %s..." % (self.name, self.description[:70])


@receiver(post_save, sender=UseCase, dispatch_uid='usecase_post_save_signal')
def post_save_usecase(sender, instance, created, using, **kwargs):
    """ Set the value of the field 'name' after creating the object """
    if created:
        instance.name = "UC/{0:05d}".format(instance.id)
        instance.save()