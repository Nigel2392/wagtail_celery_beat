# Generated by Django 4.2 on 2023-10-02 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PermissionOnlyModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'verbose_name': 'Wagtail Celery Beat Permission',
                'verbose_name_plural': 'Wagtail Celery Beat Permissions',
                'permissions': (('run_periodic_task', 'Can run periodic tasks'), ('toggle_periodic_task', 'Can toggle periodic tasks'), ('enable_periodic_task', 'Can enable periodic tasks'), ('disable_periodic_task', 'Can disable periodic tasks')),
                'managed': False,
                'default_permissions': (),
            },
        ),
    ]
