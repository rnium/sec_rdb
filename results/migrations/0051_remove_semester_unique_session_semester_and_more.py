# Generated by Django 4.2.3 on 2024-03-22 19:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0050_remove_studentpoint_with_distinction_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='semester',
            name='unique_session_semester',
        ),
        migrations.AddConstraint(
            model_name='semester',
            constraint=models.UniqueConstraint(fields=('year', 'year_semester', 'session', 'part_no', 'repeat_number'), name='unique_session_per_semester'),
        ),
    ]
