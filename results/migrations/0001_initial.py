# Generated by Django 3.2 on 2023-07-31 16:53

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('course_credit', models.FloatField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(4)])),
                ('total_marks', models.FloatField(validators=[django.core.validators.MinValueValidator(1, 'Total Marks must be greater than 0')])),
                ('part_A_marks', models.FloatField(validators=[django.core.validators.MinValueValidator(1, 'Marks must be greater than 0')])),
                ('part_B_marks', models.FloatField(validators=[django.core.validators.MinValueValidator(1, 'Marks must be greater than 0')])),
                ('incourse_marks', models.FloatField(validators=[django.core.validators.MinValueValidator(1, 'Marks must be greater than 0')])),
                ('added_in', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=3)),
                ('fullname', models.CharField(max_length=100)),
                ('dept_logo', models.ImageField(blank=True, null=True, upload_to='departments/logo/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['.jpg', '.jpeg', '.png'])])),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_year', models.IntegerField()),
                ('to_year', models.IntegerField()),
                ('batch_no', models.IntegerField()),
                ('dept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='results.department')),
            ],
            options={
                'ordering': ['from_year'],
            },
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Year must be atleast 1'), django.core.validators.MaxValueValidator(4, message='Year cannot be more than 4')])),
                ('year_semester', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Year semester must be atleast 1'), django.core.validators.MaxValueValidator(2, message='Year semester cannot be more than 2')])),
                ('semester_no', models.IntegerField(validators=[django.core.validators.MinValueValidator(1, message='Semester number must be atleast 1'), django.core.validators.MaxValueValidator(8, message='Semester number cannot be more than 8')])),
                ('added_in', models.DateTimeField(auto_now_add=True)),
                ('added_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('drop_courses', models.ManyToManyField(related_name='drop_courses', to='results.Course')),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='results.session')),
            ],
        ),
        migrations.CreateModel(
            name='CourseResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('part_A_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be less than 0')])),
                ('part_B_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be less than 0')])),
                ('incourse_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be less than 0')])),
                ('total_score', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be less than 0')])),
                ('part_A_code', models.CharField(max_length=20, null=True)),
                ('part_B_code', models.CharField(max_length=20, null=True)),
                ('grade_point', models.FloatField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0, message='Score cannot be less than 0')])),
                ('letter_grade', models.CharField(blank=True, max_length=2, null=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='results.course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.studentaccount')),
            ],
        ),
        migrations.AddField(
            model_name='course',
            name='semester',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='results.semester'),
        ),
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('at', models.DateTimeField(auto_now_add=True)),
                ('target_url', models.URLField(blank=True, null=True)),
                ('type', models.CharField(choices=[('add', 'Addition'), ('update', 'Modification'), ('delete', 'Deletion')], max_length=10)),
                ('message', models.CharField(max_length=200)),
                ('by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
