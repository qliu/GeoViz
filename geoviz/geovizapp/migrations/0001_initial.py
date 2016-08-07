# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cluster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('csrf_token', models.CharField(max_length=100, null=True, blank=True)),
            ],
            options={
                'db_table': 'cluster',
            },
        ),
        migrations.CreateModel(
            name='Instance',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('region', models.CharField(max_length=100, null=True, blank=True)),
                ('type', models.CharField(max_length=100, null=True, blank=True)),
                ('ami', models.CharField(max_length=100, null=True, blank=True)),
                ('instance_id', models.CharField(max_length=100, null=True, blank=True)),
            ],
            options={
                'db_table': 'instance',
            },
        ),
        migrations.AddField(
            model_name='cluster',
            name='instances',
            field=models.ManyToManyField(to='geovizapp.Instance', null=True, blank=True),
        ),
    ]
