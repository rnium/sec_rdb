# Generated by Django 4.2.3 on 2024-02-14 07:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_alter_adminaccount_type'),
        ('results', '0042_studentcustomdocument_doc_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='studentcustomdocument',
            name='added_by',
        ),
        migrations.AlterField(
            model_name='studentcustomdocument',
            name='student',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.studentaccount'),
        ),
    ]
