# Generated by Django 4.2.3 on 2023-08-10 18:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0009_alter_studentaccount_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='studentaccount',
            old_name='cgpa',
            new_name='credits_completed',
        ),
        migrations.AddField(
            model_name='studentaccount',
            name='total_points',
            field=models.FloatField(default=0),
        ),
    ]
