# Generated by Django 5.0.7 on 2024-08-05 18:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contact',
            old_name='main_contact',
            new_name='primary_contact',
        ),
    ]