# Generated by Django 4.2.7 on 2023-12-31 15:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('music_app', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='album',
            old_name='musician',
            new_name='album',
        ),
    ]