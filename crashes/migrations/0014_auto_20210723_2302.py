# Generated by Django 3.2.5 on 2021-07-23 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0013_auto_20210723_0725'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('project', 'name')},
        ),
    ]