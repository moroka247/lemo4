from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import reverse
from .choices import FeeFrequency, FeeBasis
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

    def __str__(self):
        return str(self.code)

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
    
    def get_absolute_url(self):
        return reverse('fund_detail', kwargs={'pk':self.pk})

class FundParameter(models.Model):
    fund = models.ForeignKey(Fund, on_delete=models.CASCADE)
    year_end = models.DateField(auto_now=False, null=True)
    fee_frequency = models.CharField(
        max_length=1,
        choices=FeeFrequency.choices,
        null=True,
        blank=True,
    )
    investment_period_fee_basis = models.CharField(
        max_length=1,
        choices=FeeBasis.choices,
        null=True,
        blank=True,
    )
    divest_period_fee_basis = models.CharField(
        max_length=1,
        choices=FeeBasis.choices,
        null=True,
        blank=True,
    )

class FundClose(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    close_date = models.DateField(auto_now=False)
    series_number = models.SmallIntegerField(null=False, default=0)
    final_close = models.BooleanField(default=False)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.series_number)
    
class CallType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.name)

class ExpenseType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return str(self.type)  

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

    def __str__(self):
        return str(self.number) + ' | ' + str(self.fund) + ' | ' + str(self.investor)

class CommittedCapital(models.Model):
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor,on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12,decimal_places=2)
    date = models.DateField(auto_now=False)
    final_close = models.BooleanField(default=False)

    def __str__(self):
        return str(self.fund) + ' | ' + str(self.investor)

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
    notice_number = models.IntegerField(null=True)
    date = models.DateField(auto_now=False, null=True)
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
    fund = models.ForeignKey(Fund,on_delete=models.CASCADE)
    period_start = models.DateField(null=False)
    period_end = models.DateField(null=False)
    update_flag = models.BooleanField(null=False)

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
    realised_proceeds = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    valuation = models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    IRR = models.DecimalField(max_digits=4,decimal_places=3,default=0.00)
    MOIC = models.DecimalField(max_digits=4,decimal_places=2,default=0.00)

    def __str__(self):
        return str(self.company) + ' | ' + str(self.fund) + ' | ' + str(self.instrument)

    def get_absolute_url(self):
        return reverse('investment_detail', kwargs={'pk':self.pk})

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

class ExpenseType(models.Model):
    name = models.CharField(max_length=100)

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

