# Generated by Django 2.0.2 on 2018-06-13 08:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('repository', '0002_auto_20180613_1521'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userinfo',
            name='nickname',
            field=models.CharField(max_length=32, null=True, verbose_name='昵称'),
        ),
    ]
