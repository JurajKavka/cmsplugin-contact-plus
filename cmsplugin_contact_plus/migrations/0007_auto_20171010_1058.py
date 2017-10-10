# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmsplugin_contact_plus', '0006_auto_20170922_1738'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contactplus',
            name='template',
            field=models.CharField(default=b'cmsplugin_contact_plus/contact.html', max_length=255, editable=False, choices=[(b'cmsplugin_contact_plus/contact.html', b'contact.html')]),
        ),
    ]
