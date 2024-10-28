# Generated by Django 3.2.12 on 2024-10-28 18:56

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('players', '0010_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='option',
            name='updated',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='notation',
            name='text',
            field=models.CharField(max_length=100),
        ),
    ]
