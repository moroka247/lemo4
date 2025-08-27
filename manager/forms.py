from django.utils import timezone
from django import forms
from django.forms import inlineformset_factory, modelformset_factory, BaseFormSet
from . models import Investor, Fund, Investment, Company, CommittedCapital, Contact, CapitalCall, InvestorContact, CallType

class InvestorForm(forms.ModelForm):
    class Meta:
        model = Investor
        fields = ['name','short_name','reg_no','category','address','city','country','post_code']

class FundForm(forms.ModelForm):
    class Meta:
        model = Fund
        fields = ['name','short_name','structure','objective','investment_period','divestment_period','currency','target_commitment',
                  'man_fee']

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

class CapitalCallForm(forms.ModelForm):
    class Meta:
        model = CapitalCall
        fields = ['date', 'call_type', 'allocation_rule', 'description', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control'
            }),
            'call_type': forms.Select(attrs={'class': 'form-control'}),
            'allocation_rule': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'E.g., Q2 2024 Capital Call for Acquisitions'
            }),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
        labels = {
            'date': 'Call Funding Date',
            'description': 'Call Description',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial date to today, but user can select any date
        self.fields['date'].initial = timezone.now().date()

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