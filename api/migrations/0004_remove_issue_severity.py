# Generated by Django 5.0.1 on 2024-12-24 01:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_issue_options_rename_issue_issue_description_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issue',
            name='severity',
        ),
    ]
