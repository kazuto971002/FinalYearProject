# Generated by Django 3.1.7 on 2021-06-23 05:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_detected_user_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='detected',
            name='person_name',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
