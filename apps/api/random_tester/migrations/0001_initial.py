# Generated by Django 2.0.2 on 2018-03-06 13:11

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SlackUser',
            fields=[
                ('slack_id', models.CharField(max_length=32, primary_key=True, serialize=False, unique=True)),
                ('name', models.CharField(max_length=512)),
            ],
        ),
    ]
