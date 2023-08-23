# Generated by Django 4.2.3 on 2023-08-22 06:14

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('account', '0014_invitetoken_to_user_dept_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='adminaccount',
            name='invitation',
        ),
        migrations.RemoveField(
            model_name='invitetoken',
            name='to_user',
        ),
        migrations.AddField(
            model_name='adminaccount',
            name='invited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='inviting_user', to=settings.AUTH_USER_MODEL),
        ),
    ]