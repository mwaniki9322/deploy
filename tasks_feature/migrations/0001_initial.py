# Generated by Django 3.2.8 on 2022-10-31 12:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('index', models.PositiveIntegerField(editable=False, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TaskTaking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('finished', models.BooleanField(default=False)),
                ('task_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks_feature.taskitem')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='tasktaking',
            constraint=models.UniqueConstraint(fields=('task_item', 'user'), name='unique_task_taking'),
        ),
    ]