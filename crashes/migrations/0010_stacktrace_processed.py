# Generated by Django 3.2.5 on 2021-07-21 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0009_event_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='stacktrace',
            name='processed',
            field=models.BooleanField(default=False),
        ),
    ]
