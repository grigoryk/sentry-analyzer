# Generated by Django 3.0.4 on 2020-03-31 00:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AssignedCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('confidence', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_id', models.CharField(max_length=255)),
                ('group_id', models.IntegerField()),
                ('message', models.CharField(blank=True, max_length=500, null=True)),
                ('categories', models.ManyToManyField(through='crashes.AssignedCategory', to='crashes.Category')),
            ],
        ),
        migrations.CreateModel(
            name='Stacktrace',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stacktrace', models.TextField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.Event')),
            ],
        ),
        migrations.CreateModel(
            name='EventTag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.Event')),
            ],
        ),
        migrations.AddField(
            model_name='assignedcategory',
            name='category',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.Category'),
        ),
        migrations.AddField(
            model_name='assignedcategory',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.Event'),
        ),
    ]
