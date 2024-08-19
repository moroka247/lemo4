# Generated by Django 5.0.7 on 2024-08-12 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='distribution',
            name='notice',
        ),
        migrations.AddField(
            model_name='distribution',
            name='date',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='distribution',
            name='notice_number',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='capitalcall',
            name='date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='capitalcall',
            name='notice_number',
            field=models.IntegerField(null=True),
        ),
    ]
