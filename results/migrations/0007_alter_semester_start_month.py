# Generated by Django 4.2.3 on 2023-08-01 05:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0006_alter_activity_options_semester_start_month'),
    ]

    operations = [
        migrations.AlterField(
            model_name='semester',
            name='start_month',
            field=models.CharField(max_length=15),
        ),
    ]
