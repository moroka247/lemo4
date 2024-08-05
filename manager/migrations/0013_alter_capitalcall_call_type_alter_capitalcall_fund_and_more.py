# Generated by Django 5.0.7 on 2024-08-03 10:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0012_rename_type_capitalcall_call_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='capitalcall',
            name='call_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.calltype'),
        ),
        migrations.AlterField(
            model_name='capitalcall',
            name='fund',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.fund'),
        ),
        migrations.AlterField(
            model_name='capitalcall',
            name='investor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.investor'),
        ),
        migrations.AlterField(
            model_name='capitalcall',
            name='notice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.noticenumber'),
        ),
        migrations.AlterField(
            model_name='distribution',
            name='distribution_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.distributiontype'),
        ),
    ]