# Generated by Django 4.2.3 on 2023-08-03 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('results', '0012_courseresult_unique_courseresult_student'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseresult',
            name='part_A_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='courseresult',
            name='part_B_code',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
