# Generated by Django 3.2.5 on 2021-08-06 19:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0019_rename_categorycounts_categorycount'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProjectEndpointCache',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processed', models.BooleanField(default=False)),
                ('json', models.TextField()),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.project')),
            ],
        ),
    ]
