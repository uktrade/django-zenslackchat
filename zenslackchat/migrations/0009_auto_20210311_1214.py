# Generated by Django 3.1.7 on 2021-03-11 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zenslackchat', '0008_outofhoursinformation'),
    ]

    operations = [
        migrations.AddField(
            model_name='outofhoursinformation',
            name='office_hours_begin',
            field=models.TimeField(default='09:00'),
        ),
        migrations.AddField(
            model_name='outofhoursinformation',
            name='office_hours_end',
            field=models.TimeField(default='17:00'),
        ),
    ]
