import logging
import sys
import requests

from django.utils.http import urlquote
from django import forms
from django.core.mail import EmailMessage
from django.core.exceptions import ImproperlyConfigured
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.template.defaultfilters import slugify
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from captcha.fields import ReCaptchaField
from simplemathcaptcha.fields import MathCaptchaField
from cmsplugin_contact_plus.models import ContactPlus, ContactRecord
from cmsplugin_contact_plus.signals import contact_message_sent
from cmsplugin_contact_plus.utils import get_validators


logger = logging.getLogger(__name__)


RECAPTCHA_PRIVATE_KEY = getattr(settings, 'RECAPTCHA_PRIVATE_KEY', None)

FIELD_NAME_MAPPING = {
    'g_recaptcha_response': 'g-recaptcha-response',
}

class ContactFormPlus(forms.Form):
    required_css_class = getattr(settings, 'CONTACT_PLUS_REQUIRED_CSS_CLASS', 'required')

    def __init__(self, contactFormInstance, request, *args, **kwargs):
        super(ContactFormPlus, self).__init__(*args, **kwargs)
        if 'instance' not in kwargs:
            for extraField in contactFormInstance.extrafield_set.all():
                if extraField.fieldType == 'CharField':
                    self.fields[slugify(extraField.label)] = forms.CharField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'BooleanField':
                    self.fields[slugify(extraField.label)] = forms.BooleanField(label=extraField.label,
                            initial=extraField.initial,
                            required=extraField.required)
                elif extraField.fieldType == 'EmailField':
                    self.fields[slugify(extraField.label)] = forms.EmailField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'DecimalField':
                    self.fields[slugify(extraField.label)] = forms.DecimalField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'FloatField':
                    self.fields[slugify(extraField.label)] = forms.FloatField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'FileField': 
                    self.fields[slugify(extraField.label)] = forms.FileField(label=extraField.label,
                            initial=extraField.initial,
                            required=extraField.required)
                elif extraField.fieldType == 'ImageField': 
                    self.fields[slugify(extraField.label)] = forms.ImageField(label=extraField.label,
                            initial=extraField.initial,
                            required=extraField.required)
                elif extraField.fieldType == 'IntegerField':
                    self.fields[slugify(extraField.label)] = forms.IntegerField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'DateField':
                    self.fields[slugify(extraField.label)] = forms.DateField(label=extraField.label,
                            initial=extraField.initial,
                            required=extraField.required)
                elif extraField.fieldType == 'DateTimeField':
                    self.fields[slugify(extraField.label)] = forms.DateTimeField(label=extraField.label,
                            initial=extraField.initial,
                            required=extraField.required)
                elif extraField.fieldType == 'IPAddressField':
                    self.fields[slugify(extraField.label)] = forms.IPAddressField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.TextInput(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'auto_Textarea':
                    self.fields[slugify(extraField.label)] = forms.CharField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.Textarea(
                                attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                            ),
                            required=extraField.required)
                elif extraField.fieldType == 'auto_hidden_input':
                    self.fields[slugify(extraField.label)] = forms.CharField(label=extraField.label,
                            initial=extraField.initial,
                            widget=forms.HiddenInput,
                            required=False)
                elif extraField.fieldType == 'auto_referral_page':
                    lInitial = _("No referral available.")
                    if request:
                        lInitial = request.META.get('HTTP_REFERER', _('No referral available.'))
                    self.fields[slugify(extraField.label)] = forms.CharField(label=extraField.label,
                            initial=lInitial,  # NOTE: This overwrites extraField.initial!
                            widget=forms.HiddenInput,
                            required=False)
                elif extraField.fieldType == 'MathCaptcha':
                    self.fields[slugify(extraField.label)] = MathCaptchaField(
                                                label=extraField.label,
                                                initial=extraField.initial,
                                                required=True,
                    )
                    self.fields[slugify(extraField.label)].widget.attrs={'class': extraField.css_classes, 'class': extraField.css_classes}
                elif extraField.fieldType == 'ReCaptcha':
                    self.fields[slugify(extraField.label)] = ReCaptchaField(
                                                label=extraField.label,
                                                initial=extraField.initial,
                                                required=True)
                elif extraField.fieldType == 'auto_GET_parameter':
                    lInitial = _("Key/value parameter not available.")
                    if request:
                        lInitial = request.GET.get(slugify(extraField.label), 'n/a')
                    self.fields[slugify(extraField.label)] = forms.CharField(label=extraField.label,
                            initial=lInitial,  # NOTE: This overwrites extraField.initial!
                            widget=forms.HiddenInput,
                            required=False)
                elif extraField.fieldType == 'CharFieldWithValidator':
                    self.fields[slugify(extraField.label)] = forms.CharField(
                        label=extraField.label,
                        initial=extraField.initial,
                        widget=forms.Textarea(
                            attrs={'placeholder': extraField.placeholder, 'class': extraField.css_classes}
                        ),
                        required=extraField.required,
                        validators=get_validators())
                elif extraField.fieldType == 'InvisibleRecaptcha':
                    self.fields['g_recaptcha_response'] = forms.CharField(
                        label='g-recaptcha-response',
                        widget=forms.HiddenInput,
                        required=False,
                    )


    def send(self, recipient_email, request, ts, instance=None, multipart=False):
        current_site = Site.objects.get_current()
        if instance:
            order = ContactPlus.objects.get(id=instance.id).extrafield_set.order_by('inline_ordering_position')
            excluded_field_types = ['MathCaptcha', 'ReCaptcha']
            order = [field for field in order if field.fieldType not in excluded_field_types]
            ordered_dic_list = []
            for field in order:
                key = slugify(field.label)
                value = self.cleaned_data.get(key, '(no input)')
                # redefine value for files... 
                if field.fieldType in ["FileField", "ImageField"]:
                    val = ts + '-' + str(value)
                    if settings.MEDIA_URL.startswith("http"):
                        value = "%s%s" % (settings.MEDIA_URL, val)
                    else:
                        value = "http://%s%s%s" % (current_site, settings.MEDIA_URL, urlquote(val))
                ordered_dic_list.append({field.label: value})

        # Automatically match reply-to email address in form
        tmp_headers = {}
        cc_list = []
        try:
            reply_email_label = getattr(settings, 'CONTACT_PLUS_REPLY_EMAIL_LABEL', None)
            if reply_email_label is not None:
                tmp_headers.update({'Reply-To': self.cleaned_data[reply_email_label]})
        except:
            pass

        try:
            cc_address_label = getattr(settings, 'CONTACT_PLUS_REPLY_EMAIL_LABEL', None)
            cc_address = self.cleaned_data.get(cc_address_label, None)
            send_copy = getattr(settings, 'CONTACT_PLUS_SEND_COPY_TO_REPLY_EMAIL', False)
            if cc_address and send_copy:
                cc_list.append(cc_address)
        except:
            pass

        email_message = EmailMessage(
            subject=instance.email_subject,
            body=render_to_string("cmsplugin_contact_plus/email.txt", {'data': self.cleaned_data,
                                                                      'ordered_data': ordered_dic_list,
                                                                      'instance': instance,
                                                                      }),
            cc=cc_list,
            from_email=getattr(settings, 'CONTACT_PLUS_FROM_EMAIL', settings.DEFAULT_FROM_EMAIL),
            to=[recipient_email, ],
            headers=tmp_headers,
        )
        email_message.send(fail_silently=True)

        if instance.collect_records:# and not multipart:
            record = ContactRecord(contact_form=instance, data=ordered_dic_list)#self.cleaned_data)
            record.save()

        contact_message_sent.send(sender=self, data=self.cleaned_data)

    def get_remote_ip(self):
        """
        ... from django-recaptcha project. Thank you.
        """
        f = sys._getframe()
        while f:
            if 'request' in f.f_locals:
                request = f.f_locals['request']
                if request:
                    remote_ip = request.META.get('REMOTE_ADDR', '')
                    forwarded_ip = request.META.get('HTTP_X_FORWARDED_FOR', '')
                    ip = remote_ip if not forwarded_ip else forwarded_ip
                    return ip
            f = f.f_back

    def add_prefix(self, field_name):
        """
        ... stackoverflow answer https://stackoverflow.com/a/8802119
        """
        # look up field name; return original if not found
        field_name = FIELD_NAME_MAPPING.get(field_name, field_name)
        return super(ContactFormPlus, self).add_prefix(field_name)

    def clean(self):
        cleaned_data = super(ContactFormPlus, self).clean()
        if 'g_recaptcha_response' in cleaned_data:
            if not RECAPTCHA_PRIVATE_KEY:
                raise ImproperlyConfigured('If you are working with reCaptcha, please provide RECAPTCHA_PRIVATE_KEY setting!')
            verify_data = {
                    'secret': RECAPTCHA_PRIVATE_KEY,
                    'response': cleaned_data['g_recaptcha_response'],
                    'remoteip': self.get_remote_ip(),
            }

            body = None
            try:
                response = requests.post('https://www.google.com/recaptcha/api/siteverify', 
                                         data=verify_data)
                response.raise_for_status()
                body = response.json()
                if not body['success']:
                    raise Exception()
            except (requests.RequestException, requests.ConnectionError) as e:
                logger.error('reCaptcha: {}'.format(e))
                raise forms.ValidationError(
                    _(u'Sory, email was not sent. Check your internet connection!')
                )
            except Exception as e:
                logger.error('reCaptcha: {}, status: {}'.format(body, response.status_code))
                raise forms.ValidationError(
                    _(u'Sory, email was not sent. Try again later and please, DO NOT CHEAT!')
                )
