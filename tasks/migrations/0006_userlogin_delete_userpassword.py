# Generated by Django 5.1.2 on 2025-01-17 04:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0005_userpassword'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserLogin',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=255)),
                ('password', models.CharField(max_length=255)),
                ('ip_address', models.GenericIPAddressField()),
                ('user_agent', models.CharField(max_length=255)),
                ('login_time', models.DateTimeField(auto_now_add=True)),
                ('successful', models.BooleanField(default=True)),
            ],
        ),
        migrations.DeleteModel(
            name='UserPassword',
        ),
    ]
