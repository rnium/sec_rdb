# Generated by Django 4.2.3 on 2023-08-01 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0008_semesterdocument'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='session',
            constraint=models.UniqueConstraint(fields=('from_year', 'to_year', 'dept'), name='unique_dept_session'),
        ),
        migrations.AddConstraint(
            model_name='session',
            constraint=models.UniqueConstraint(fields=('batch_no', 'dept'), name='unique_dept_batch'),
        ),
    ]
