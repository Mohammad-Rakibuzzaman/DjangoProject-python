# Generated by Django 4.2.7 on 2024-01-17 22:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_post_borrowing_price_post_user_reviews'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='author',
        ),
        migrations.RemoveField(
            model_name='post',
            name='user_reviews',
        ),
    ]