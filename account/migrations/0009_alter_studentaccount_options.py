# Generated by Django 4.2.3 on 2023-08-10 14:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0008_studentaccount_is_regular'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='studentaccount',
            options={'ordering': ['-is_regular', 'registration']},
        ),
    ]
