# Generated by Django 5.0.7 on 2024-08-02 18:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0009_alter_fund_life'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='IncomeType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
            ],
        ),
        migrations.RenameModel(
            old_name='allocation_rule',
            new_name='AllocationRule',
        ),
        migrations.RenameModel(
            old_name='call_type',
            new_name='CallType',
        ),
        migrations.RenameModel(
            old_name='capital_call',
            new_name='CapitalCall',
        ),
        migrations.RenameModel(
            old_name='committed_capital',
            new_name='CommittedCapital',
        ),
        migrations.RenameModel(
            old_name='distribution_type',
            new_name='DistributionType',
        ),
        migrations.RenameModel(
            old_name='fund_close',
            new_name='FundClose',
        ),
        migrations.RenameModel(
            old_name='fund_structure',
            new_name='FundStructure',
        ),
        migrations.RenameModel(
            old_name='investor_documents',
            new_name='InvestorDocument',
        ),
        migrations.RenameModel(
            old_name='investor_type',
            new_name='InvestorType',
        ),
        migrations.RenameModel(
            old_name='notice_number',
            new_name='NoticeNumber',
        ),
        migrations.AlterModelOptions(
            name='company',
            options={'verbose_name_plural': 'Companies'},
        ),
        migrations.AlterModelOptions(
            name='country',
            options={'verbose_name_plural': 'Countries'},
        ),
        migrations.AlterModelOptions(
            name='currency',
            options={'verbose_name_plural': 'Currencies'},
        ),
        migrations.AlterModelOptions(
            name='industry',
            options={'verbose_name_plural': 'Industries'},
        ),
        migrations.RemoveField(
            model_name='fund',
            name='commitment',
        ),
        migrations.RemoveField(
            model_name='fund',
            name='distributions',
        ),
        migrations.RemoveField(
            model_name='fund',
            name='drawn_capital',
        ),
        migrations.RemoveField(
            model_name='fund',
            name='portfolio_count',
        ),
        migrations.RemoveField(
            model_name='fund',
            name='undrawn_capital',
        ),
        migrations.RemoveField(
            model_name='investor',
            name='contact_email',
        ),
        migrations.RemoveField(
            model_name='investor',
            name='key_contact',
        ),
        migrations.RemoveField(
            model_name='investor',
            name='phone',
        ),
        migrations.AlterField(
            model_name='contact',
            name='reports',
            field=models.BooleanField(default=True),
        ),
        migrations.CreateModel(
            name='OperatingExpense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fund', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.fund')),
                ('income_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.expensetype')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.investor')),
            ],
        ),
        migrations.CreateModel(
            name='OperatingIncome',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12)),
                ('fund', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.fund')),
                ('income_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.incometype')),
                ('investor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.investor')),
            ],
        ),
    ]
