from django.contrib import admin
from .models import *
from .forms import FundParameterForm

admin.site.register(Currency)
admin.site.register(Country)
admin.site.register(Company)
admin.site.register(Industry)
admin.site.register(FundStructure)
admin.site.register(Fund)
admin.site.register(FundClose)
admin.site.register(InvestorType)
admin.site.register(Investor)
admin.site.register(Contact)
admin.site.register(Instrument)
admin.site.register(Investment)
admin.site.register(CommittedCapital)
admin.site.register(NoticeNumber)
admin.site.register(CallType)
admin.site.register(CapitalCall)
admin.site.register(DistributionType)
admin.site.register(Disbursement)

@admin.register(FundParameter)
class FundParameterAdmin(admin.ModelAdmin):
    form = FundParameterForm
    list_display = ['fund', 'vat_registered', 'vat_rate', 'fee_frequency']
    list_editable = ['vat_registered', 'vat_rate']

@admin.register(ManagementFees)
class ManagementFeesAdmin(admin.ModelAdmin):
    list_display = [
        'fund', 
        'period_start_date', 
        'period_end_date', 
        'gross_fee_amount',
        'vat_applicable',
        'vat_amount',
        'total_fee_amount',
        'paid'
    ]

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# Simple admin for ExpenseType - remove any complex fields temporarily
@admin.register(ExpenseType)
class ExpenseTypeAdmin(admin.ModelAdmin):
    list_display = ['name']  # Only show name for now
    search_fields = ['name']

@admin.register(InvestmentAllocation)
class InvestmentAllocationAdmin(admin.ModelAdmin):
    list_display = ['investment', 'investor', 'allocated_amount']
    search_fields = ['investment__company__name', 'investor__name']