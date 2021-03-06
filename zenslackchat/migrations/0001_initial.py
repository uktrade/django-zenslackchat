# Generated by Django 3.1.1 on 2020-09-10 11:01

from django.db import migrations, models
import zenslackchat.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('team_name', models.CharField(max_length=200)),
                ('team_id', models.CharField(max_length=20)),
                ('bot_user_id', models.CharField(max_length=20)),
                ('bot_access_token', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='ZenSlackChat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=22)),
                ('chat_id', models.CharField(max_length=20)),
                ('ticket_id', models.CharField(max_length=20)),
                ('active', models.BooleanField(default=True)),
                ('opened', models.DateTimeField(default=zenslackchat.models.utcnow)),
                ('closed', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'unique_together': {('channel_id', 'chat_id')},
            },
        ),
    ]
