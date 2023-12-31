# Generated by Django 4.2.3 on 2023-08-04 12:22

import django.contrib.auth.models
from django.db import migrations, models
import results.models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0014_alter_courseresult_letter_grade'),
    ]

    operations = [
        migrations.AddField(
            model_name='semesterdocument',
            name='tabulation_sheet_render_by',
            field=models.DateTimeField(blank=True, null=True, verbose_name=django.contrib.auth.models.User),
        ),
        migrations.AddField(
            model_name='semesterdocument',
            name='tabulation_sheet_render_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='semesterdocument',
            name='tabulation_sheet',
            field=models.FileField(blank=True, null=True, upload_to=results.models.SemesterDocument.filepath),
        ),
        migrations.AlterField(
            model_name='semesterdocument',
            name='tabulation_thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to=results.models.SemesterDocument.filepath),
        ),
    ]
