# Generated by Django 5.0.7 on 2024-08-05 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0002_rename_main_contact_contact_primary_contact'),
    ]

    operations = [
        migrations.AlterField(
            model_name='committedcapital',
            name='fund_interest',
            field=models.DecimalField(decimal_places=3, max_digits=4, null=True),
        ),
    ]