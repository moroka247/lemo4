# Generated by Django 5.0.7 on 2024-08-04 08:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0013_alter_capitalcall_call_type_alter_capitalcall_fund_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnrealisedTypes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='UnrealisedGainsOrLosses',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fund', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.fund')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.investor')),
                ('unrealised_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.unrealisedtypes')),
            ],
        ),
    ]
