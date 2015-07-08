from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.sites.models import Site
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template import Context
from django.template.loader import get_template
from django.utils import timezone
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from allauth.account.models import EmailAddress
from base.models import BaseModel
from .signals import register_approved, register_rejected

SENDER_EMAIL = getattr(settings, 'SENDER_EMAIL', '')


""" Adding additional fields to EmailAddress """
if not hasattr(EmailAddress, 'admin_approval'):
    field = models.CharField(choices=[('pending', 'Pending'),
                                               ('approved', 'Approved'),
                                               ('rejected', 'Rejected')], max_length=32, db_index=True, default='pending')
    field.contribute_to_class(EmailAddress, 'admin_approval')


if not hasattr(EmailAddress, 'reject_reason'):
    field = models.TextField(null=True, blank=True)
    field.contribute_to_class(EmailAddress, 'reject_reason')


if not hasattr(EmailAddress, 'created_at'):
    field = models.DateTimeField(default=timezone.now)
    field.contribute_to_class(EmailAddress, 'created_at')


if not hasattr(EmailAddress, 'modified_at'):
    field = models.DateTimeField(auto_now=True)
    field.contribute_to_class(EmailAddress, 'modified_at')


if not hasattr(EmailAddress, 'modified_by'):
    field = models.ForeignKey(User, null=True, related_name='+')
    field.contribute_to_class(EmailAddress, 'modified_by')


""" Adding additional methods to EmailAddress """
def action_approve(self):
    self.admin_approval = 'approved'
    self.save()
    register_approved.send(sender=self.__class__, instance=self)

if not hasattr(EmailAddress, 'action_approve'):
    EmailAddress.action_approve = action_approve


def action_reject(self, reject_reason=None):
    self.admin_approval = 'rejected'
    self.reject_reason = reject_reason
    self.save()
    # send signal
    register_rejected.send(sender=self.__class__, instance=self)


if not hasattr(EmailAddress, 'action_reject'):
    EmailAddress.action_reject = action_reject



# This method will send an email when registration gets approved
@receiver(register_approved)
def email_on_approve(sender, instance, **kwargs):

    site_url = _current_site_url()
    login_url = site_url + reverse('account_login')

    send_mail(_('Registration Request Approved'), get_template('register/email/email_registration_approved.txt').render(
        Context({
            'user': instance.user,
            'current_site': kwargs["site"] if "site" in kwargs else Site.objects.get_current(),
            'login_url': login_url,
        })
    ), SENDER_EMAIL, [instance.email], fail_silently=True)


# This method will send an email when registration gets approved
@receiver(register_rejected)
def email_on_reject(sender, instance, **kwargs):

    send_mail(_('Registration Request Rejected'), get_template('register/email/email_registration_rejected.txt').render(
        Context({
            'user': instance.user,
            'current_site': kwargs["site"] if "site" in kwargs else Site.objects.get_current(),
            'reject_reason': instance.reject_reason,
        })
    ), SENDER_EMAIL, [instance.email], fail_silently=True)



def _current_site_url():
    """Returns fully qualified URL (no trailing slash) for the current site."""
    from django.contrib.sites.models import Site

    current_site = Site.objects.get_current()
    protocol = getattr(settings, 'MY_SITE_PROTOCOL', 'http')
    port = getattr(settings, 'MY_SITE_PORT', '')
    url = '%s://%s' % (protocol, current_site.domain)
    if port:
        url += ':%s' % port
    return url