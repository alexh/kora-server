# Generated by Django 5.0.1 on 2024-12-24 01:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_issue'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='issue',
            options={},
        ),
        migrations.RenameField(
            model_name='issue',
            old_name='issue',
            new_name='description',
        ),
        migrations.AddField(
            model_name='issue',
            name='severity',
            field=models.CharField(default='low', max_length=20),
        ),
    ]
