# Generated by Django 3.2.5 on 2021-07-20 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0008_auto_20210720_0109'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='info',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]