# Generated by Django 3.2.5 on 2021-08-12 20:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0028_processeventtag'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='categorycount',
            unique_together={('keyed_tag', 'category', 'date')},
        ),
    ]
