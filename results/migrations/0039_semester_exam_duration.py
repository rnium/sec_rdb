# Generated by Django 4.2.3 on 2024-01-20 09:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0038_alter_course_added_in'),
    ]

    operations = [
        migrations.AddField(
            model_name='semester',
            name='exam_duration',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
