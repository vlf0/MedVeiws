# Generated by Django 4.2.4 on 2023-09-07 10:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('WebApp', '0002_connectingtokis_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connectingtokis',
            name='active',
            field=models.BooleanField(default=False, help_text='If you want use some DB - you need turn on the checkbox.'),
        ),
    ]
