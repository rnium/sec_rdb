# Generated by Django 4.2.3 on 2023-08-11 05:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0010_rename_cgpa_studentaccount_credits_completed_and_more'),
        ('results', '0017_alter_semesterdocument_tabulation_sheet_render_by'),
    ]

    operations = [
        migrations.CreateModel(
            name='SemesterEnroll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester_credits', models.FloatField(default=0)),
                ('semester_points', models.FloatField(default=0)),
                ('semester_gpa', models.FloatField(default=0)),
                ('courses', models.ManyToManyField(related_name='enrolled_courses', to='results.course')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='results.semester')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.studentaccount')),
            ],
        ),
        migrations.AddConstraint(
            model_name='semesterenroll',
            constraint=models.UniqueConstraint(fields=('semester', 'student'), name='one_enroll_per_semester'),
        ),
    ]
