from decimal import Decimal
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import reverse
from .choices import FeeFrequency, FeeBasis, Month
from django.db.models import Q

class InvestorType(models.Model):
    category = models.CharField(max_length=100)

    def __str__(self):
        return str(self.category)

class Country(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Countries'

    def __str__(self):
        return str(self.name)

class Investor(models.Model):
    name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=10)
    logo = models.ImageField(upload_to='investors',default='no_picture.png', null=True)
    reg_no = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=20)
    country = models.ForeignKey(Country,on_delete=models.PROTECT)
    post_code = models.CharField(max_length=10)
    category = models.ForeignKey(InvestorType, on_delete=models.DO_NOTHING)

    def __str__(self):
        return str(self.name)
    
    def get_absolute_url(self):
        return reverse('investor_detail', kwargs={'pk':self.pk})

class Contact(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    id_number = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email_address = models.EmailField(max_length=100)

    def __str__(self):
        return str(self.name) + ' ' + str(self.surname)

    def get_absolute_url(self):
        return reverse('contact_detail', kwargs={'pk':self.pk})

class InvestorContact(models.Model):
    contact = models.ForeignKey(Contact,on_delete=models.CASCADE,null=False)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE,null=False)
    primary_contact = models.BooleanField(default=False)
    adv_board_rep = models.BooleanField(default=False)
    invest_comm_rep = models.BooleanField(default=False)
    reports = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['contact', 'investor'], name='uniq_contact_investor'),
            models.UniqueConstraint(
                fields=['investor'],
                condition=Q(primary_contact=True),
                name='uniq_primary_contact_per_investor'
            )
        ]

    def save(self, *args, **kwargs):
        # Automatically unset any other primary for this investor
        if self.primary_contact:
            InvestorContact.objects.filter(
                investor=self.investor,
                primary_contact=True
            ).exclude(pk=self.pk).update(primary_contact=False)
        super().save(*args, **kwargs)

class InvestorDocument(models.Model):
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE,null=False)
    description = models.CharField(max_length=255,null=False)
    document = models.FileField(upload_to='investors',null=True)

class Currency(models.Model):
    name = models.CharField(max_length=50)   
    code = models.CharField(max_length=4)
    symbol = models.CharField(max_length=1, null=False)

    def __str__(self):
        return f"{self.symbol} ({self.code})"

    class Meta:
        verbose_name_plural = 'Currencies'

class FundStructure(models.Model):
    structure = models.CharField(max_length=100)

    def __str__(self):
        return str(self.structure)

class Fund(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=20)
    objective = models.TextField(max_length=300, blank=True)
    investment_period = models.IntegerField(default=0,)
    divestment_period = models.IntegerField(default=0)
    life = models.IntegerField(default=0)
    target_commitment = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    man_fee = models.DecimalField(max_digits=4, default=0.00,decimal_places=3)
    structure = models.ForeignKey(FundStructure,on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency,on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)
    
    def save(self, *args, **kwargs):
        self.life = self.investment_period + self.divestment_period
        super().save(*args, **kwargs)

    def currency_symbol(self):
        return self.currency.symbol    
    
    def get_absolute_url(self):
        return reverse('fund_detail', kwargs={'pk':self.pk})

    def get_first_commitment_date(self):
        """Return the date of the first committed capital for this fund"""
        first_commitment = CommittedCapital.objects.filter(
            fund=self
        ).order_by('date').first()
        
        if first_commitment:
            return first_commitment.date
        return None

class FundParameter(models.Model):
    fund = models.OneToOneField(Fund, on_delete=models.CASCADE, related_name='parameters')
    
    # VAT Configuration
    vat_registered = models.BooleanField(
        default=False,
        help_text="Whether the fund manager is VAT registered"
    )
    vat_rate = models.DecimalField(
        max_digits=5, 
        decimal_places=3,
        default=Decimal('0.15'),  # 15% default VAT rate
        help_text="VAT rate to apply (e.g., 0.15 for 15%)"
    )

    # Fee Calculation Configuration
    fee_frequency = models.CharField(
        max_length=1,
        choices=FeeFrequency.choices,
        default=FeeFrequency.QUARTERLY
    )
    investment_period_fee_basis = models.CharField(
        max_length=1,
        choices=FeeBasis.choices,
        default=FeeBasis.COMMITTED_CAPITAL
    )
    divest_period_fee_basis = models.CharField(
        max_length=1,
        choices=FeeBasis.choices,
        default=FeeBasis.INVESTED_CAPITAL
    )
    
    # Fiscal Year Configuration
    fiscal_year_end_month = models.CharField(
        max_length=3,
        choices=Month.choices,
        default=Month.DECEMBER
    )
    
    # Flexible Period End Configuration
    period1_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period2_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period3_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period4_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period5_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period6_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period7_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period8_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period9_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period10_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period11_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    period12_end_month = models.CharField(max_length=3, choices=Month.choices, blank=True, null=True)
    
    investment_period_end_date = models.DateField()
    
    class Meta:
        verbose_name = "Fund Parameter"
        verbose_name_plural = "Fund Parameters"

    def get_period_end_months(self):
        """Return list of period end months based on frequency and configuration"""
        # Get all non-empty custom period end months
        custom_months = []
        for i in range(1, 13):
            field_name = f'period{i}_end_month'
            month_value = getattr(self, field_name)
            if month_value:
                custom_months.append(month_value)
        
        # If custom months are defined, use them
        if custom_months:
            return custom_months
        
        # Default behavior based on frequency
        if self.fee_frequency == FeeFrequency.ANNUALLY:
            return [self.fiscal_year_end_month]
        
        elif self.fee_frequency == FeeFrequency.SEMI_ANNUALLY:
            # Default: 6 months apart
            month_num = Month.values.index(self.fiscal_year_end_month) + 1
            mid_year_num = (month_num - 6) % 12 or 12
            mid_year_month = Month.values[mid_year_num - 1]
            return [mid_year_month, self.fiscal_year_end_month]
        
        elif self.fee_frequency == FeeFrequency.QUARTERLY:
            # Default: standard quarters
            month_num = Month.values.index(self.fiscal_year_end_month) + 1
            q1_num = (month_num - 9) % 12 or 12
            q2_num = (month_num - 6) % 12 or 12
            q3_num = (month_num - 3) % 12 or 12
            return [
                Month.values[q1_num - 1],
                Month.values[q2_num - 1], 
                Month.values[q3_num - 1],
                self.fiscal_year_end_month
            ]
        
        elif self.fee_frequency == FeeFrequency.MONTHLY:
            return list(Month.values)
        
        return []

class FundClose(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    close_date = models.DateField(auto_now=False)
    series_number = models.SmallIntegerField(null=False, default=0)
    final_close = models.BooleanField(default=False)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.series_number)
    
class CallType(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=(
        ('INVESTMENT', 'Investment'),
        ('EXPENSE', 'Expense'),
        ('FEE', 'Fee')
    ), default='EXPENSE')

    def __str__(self):
        return str(self.name)

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.name)

class ExpenseType(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return str(self.name)

class DistributionType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

class AllocationRule(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255,blank=True)

    def __str__(self):
        return str(self.name)

class NoticeNumber(models.Model):
    date = models.DateField(auto_now=False)
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.SET_NULL, null=True, blank=True)
    number = models.SmallIntegerField(default=500)
    notice_code = models.CharField(max_length=50, blank=True)

    def save(self, *args, **kwargs):
        if not self.notice_code:
            # Get the next notice number for this specific fund
            last_notice = NoticeNumber.objects.filter(
                fund=self.fund
            ).order_by('-id').first()
            
            if last_notice and last_notice.notice_code:
                try:
                    # Extract the number part and increment
                    last_number = int(last_notice.notice_code)
                    next_number = last_number + 1
                except (ValueError, AttributeError):
                    next_number = 1
            else:
                next_number = 1
                
            self.notice_code = str(next_number)
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.notice_code} | {self.fund.name} | {self.investor.name if self.investor else 'Batch'}"

class CommittedCapital(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE,null=False)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE,null=False)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    date = models.DateField(auto_now=False)
    final_close = models.BooleanField(default=False)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.investor)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(investor__isnull=True),
                name='investor_required'
            )
        ]

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=~Q(fund__isnull=True),
                name='fund_required'
            )
        ]

class Distribution(models.Model):
    notice_number = models.IntegerField(null=True)
    date = models.DateField(auto_now=False, null=True)
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    distribution_type = models.ForeignKey(DistributionType,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    allocation_percentage = models.DecimalField(max_digits=3,decimal_places=2)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.notice_number) + ' | ' + str(self.distribution_type)

class CapitalCall(models.Model):
    notice_number = models.ForeignKey(NoticeNumber, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(auto_now=False, null=True)
    due_date = models.DateField(null=True, blank=True) 
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    call_type = models.ForeignKey(CallType,on_delete=models.CASCADE)
    allocation_rule = models.ForeignKey(AllocationRule, on_delete=models.CASCADE)
    description = models.CharField(max_length=50, null=True)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.notice_number) + ' | ' + str(self.call_type)

    class Meta:
        ordering = ['-date', 'investor__name']

class ManagementFees(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    calculated_basis = models.DecimalField(max_digits=15, decimal_places=2)
    basis_type = models.CharField(max_length=2, choices=FeeBasis.choices)
    gross_fee_amount = models.DecimalField(max_digits=15, decimal_places=2)
    applicable_fee_rate = models.DecimalField(max_digits=6, decimal_places=4)
    prorated = models.BooleanField(default=True)
    capital_call = models.ForeignKey(
        'CapitalCall', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='management_fees'
    )
    paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    prorated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # VAT fields
    vat_applicable = models.BooleanField(default=False)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=3, default=Decimal('0.00'))
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    @property
    def calculation_date(self):
        """Backward compatibility property - returns the date part of created_at"""
        return self.created_at.date()

    class Meta:
        verbose_name_plural = "Management fees"
        ordering = ['-period_end_date', 'fund']
        unique_together = ['fund', 'period_start_date', 'period_end_date']
    
    def __str__(self):
        return f"{self.fund.name} - {self.period_start_date} to {self.period_end_date} - ${self.gross_fee_amount:,.2f}"

class Instrument(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=400)

    def __str__(self):
        return str(self.name)

class Industry(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Industries'

    def __str__(self):
        return str(self.name)

class Company(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=50)
    registration_no = models.CharField(max_length=20)
    description = models.TextField(max_length=400,null=True)
    industry = models.ForeignKey(Industry,on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = 'Companies'

    def __str__(self):
        return str(self.name)
    
    def get_absolute_url(self):
        return reverse('company_detail', kwargs={'pk':self.pk})

class Investment(models.Model):
    company = models.ForeignKey(Company,on_delete=models.CASCADE)
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument,on_delete=models.PROTECT)
    committed_amount = models.DecimalField(max_digits=12, decimal_places=2,default=0.00)
    invested_amount = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    date = models.DateField(null=True, blank=True)
    realised_proceeds = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    valuation = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    IRR = models.DecimalField(max_digits=4,decimal_places=3,default=0.00)
    MOIC = models.DecimalField(max_digits=4,decimal_places=2,default=0.00)

    def __str__(self):
        return str(self.company) + ' | ' + str(self.fund) + ' | ' + str(self.instrument)

    def get_absolute_url(self):
        return reverse('investment_detail', kwargs={'pk':self.pk})

class InvestmentAllocation(models.Model):
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocation_percentage = models.DecimalField(max_digits=5, decimal_places=4)  # 0.0000 to 1.0000
    
    class Meta:
        unique_together = ('investment', 'investor')
    
    def __str__(self):
        return f"{self.investor} - {self.investment}: {self.allocation_percentage:.2%}"

class Valuation(models.Model):
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, related_name='valuations')
    valuation_date = models.DateField()  # The "as of" date for this valuation
    value = models.DecimalField(max_digits=16, decimal_places=2)  # The value on that date
    # Optional but recommended:
    note = models.TextField(blank=True)  # Source of valuation (e.g., "Board Update", "Portfolio Manager Estimate")
    created_at = models.DateTimeField(auto_now_add=True)  # Audit trail

    class Meta:
        unique_together = ['investment', 'valuation_date']  # One valuation per investment per day

class Disbursement(models.Model):
    date = models.DateField(auto_now=False, blank=False, null=False)
    investment = models.ForeignKey(Investment,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

    def __str__(self) -> str:
        return super().__str__()

class IncomeType(models.Model):
    name = models.CharField(max_length=100)

class OperatingIncome(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    income_type = models.ForeignKey(IncomeType,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

class OperatingExpense(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    expense_type = models.ForeignKey(ExpenseType,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

class UnrealisedGains(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

class UnrealisedLosses(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

class NetAssetValue(models.Model):
    date = models.DateField(auto_now=False, null=False)
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)

