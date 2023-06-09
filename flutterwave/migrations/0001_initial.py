# Generated by Django 3.2.8 on 2022-10-31 12:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FWPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event', models.JSONField()),
                ('data', models.JSONField(null=True)),
                ('id_2', models.CharField(editable=False, max_length=150, unique=True)),
                ('is_processed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10, null=True)),
            ],
        ),
    ]
