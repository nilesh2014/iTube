# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-19 17:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('itube', '0002_auto_20170419_1659'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userlog',
            name='favourite',
        ),
    ]