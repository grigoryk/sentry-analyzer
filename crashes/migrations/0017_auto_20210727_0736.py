# Generated by Django 3.2.5 on 2021-07-27 07:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('crashes', '0016_computedtrend'),
    ]

    operations = [
        migrations.RenameField(
            model_name='computedtrend',
            old_name='trend',
            new_name='fatal_trend',
        ),
        migrations.RemoveField(
            model_name='computedtrend',
            name='is_info',
        ),
        migrations.AddField(
            model_name='computedtrend',
            name='info_trend',
            field=models.FloatField(default=1),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='CategoryCounts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('info_count', models.IntegerField()),
                ('fatal_count', models.IntegerField()),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crashes.category')),
            ],
        ),
    ]
