# Generated by Django 2.1.3 on 2018-12-26 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0004_auto_20181206_1057'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='die',
            name='selected',
        ),
    ]
