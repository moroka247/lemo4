from django.utils import timezone
from django import forms
from django.forms import formset_factory, inlineformset_factory, modelformset_factory, BaseFormSet
from . models import (
    Investor, Fund, Investment, Company, CommittedCapital, Contact, CapitalCall, 
    InvestorContact, CallType, AllocationRule, FundParameter
)
from .choices import FeeFrequency, FeeBasis, Month

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = ['name','short_name','reg_no','category','address','city','country','post_code']

class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name','short_name','structure','objective','investment_period','divestment_period','currency','target_commitment',
                  'man_fee']

class FundParameterForm(forms.ModelForm):
    class Meta:
        model = FundParameter
        fields = '__all__'
        widgets = {
            'investment_period_end_date': forms.DateInput(attrs={'type': 'date'}),
            'fee_frequency': forms.Select(choices=FeeFrequency.choices),
            'investment_period_fee_basis': forms.Select(choices=FeeBasis.choices),
            'divest_period_fee_basis': forms.Select(choices=FeeBasis.choices),
            'vat_rate': forms.NumberInput(attrs={'step': '0.001', 'min': '0', 'max': '1'}),
            'fiscal_year_end_month': forms.Select(choices=Month.choices),
            'period1_end_month': forms.Select(choices=Month.choices),
            'period2_end_month': forms.Select(choices=Month.choices),
            'period3_end_month': forms.Select(choices=Month.choices),
            'period4_end_month': forms.Select(choices=Month.choices),
            'period5_end_month': forms.Select(choices=Month.choices),
            'period6_end_month': forms.Select(choices=Month.choices),
            'period7_end_month': forms.Select(choices=Month.choices),
            'period8_end_month': forms.Select(choices=Month.choices),
            'period9_end_month': forms.Select(choices=Month.choices),
            'period10_end_month': forms.Select(choices=Month.choices),
            'period11_end_month': forms.Select(choices=Month.choices),
            'period12_end_month': forms.Select(choices=Month.choices),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make period fields not required
        for i in range(1, 13):
            self.fields[f'period{i}_end_month'].required = False

    def clean_vat_rate(self):
        vat_rate = self.cleaned_data.get('vat_rate')
        if vat_rate < 0 or vat_rate > 1:
            raise forms.ValidationError("VAT rate must be between 0 and 1 (e.g., 0.15 for 15%)")
        return vat_rate

class InvestmentForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ['company','fund','instrument','committed_amount']

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name','short_name','registration_no','description','industry','country']

class CommittedCapitalForm(forms.ModelForm):
    class Meta:
        model = CommittedCapital
        fields = ['investor', 'amount', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'investor': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().date()
        
        # Hide investor field if it's pre-selected
        if 'investor' in self.initial:
            self.fields['investor'].widget = forms.HiddenInput()
        
CommittedCapitalFormSet = inlineformset_factory(
    Fund,
    CommittedCapital,
    form=CommittedCapitalForm,
    extra=1,
    can_delete=True,
    fields=['investor', 'amount', 'date']
)

class CapitalCallDateForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'class': 'form-control'
        }),
        label='Call Funding Date'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].initial = timezone.now().date()

class CapitalCallItemForm(forms.Form):
    call_type = forms.ModelChoiceField(
        queryset=CallType.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Call Type'
    )
    allocation_rule = forms.ModelChoiceField(
        queryset=AllocationRule.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Allocation Rule'
    )
    description = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Description of capital call item'
        }),
        label='Description'
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Amount'
        }),
        label='Amount'
    )

CapitalCallItemFormSet = formset_factory(
    CapitalCallItemForm,
    extra=3,
    can_delete=True,
    can_order=False
)

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields= ['name','surname','phone_number','email_address']

class InvestorContactForm(forms.ModelForm):
    class Meta:
        model = InvestorContact
        fields = ['investor', 'primary_contact', 'adv_board_rep', 'invest_comm_rep', 'reports']

    def __init__(self, *args, contact=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.contact = contact
        if contact:
            linked = InvestorContact.objects.filter(contact=contact).values_list('investor_id', flat=True)
            self.fields['investor'].queryset = Investor.objects.exclude(id__in=linked)
            
            if not self.fields['investor'].queryset.exists():
                self.fields['investor'].help_text = "No available investors to link"

class InvestorContactUpdateForm(forms.ModelForm):
    class Meta:
        model = InvestorContact
        fields = ['primary_contact', 'adv_board_rep', 'invest_comm_rep', 'reports']