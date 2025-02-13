from django import forms
from django.forms import inlineformset_factory, modelformset_factory, BaseFormSet
from . models import Investor, Fund, Investment, Company, CommittedCapital, Contact, CapitalCall, NoticeNumber, CallType

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

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields= ['primary_contact','name','surname','phone_number','email_address','investor']

ContactFormSet = inlineformset_factory(Investor, Contact, form=ContactForm, extra=1)

class CommittedCapitalForm(forms.ModelForm):
    class Meta:
        model = CommittedCapital
        fields = ['investor', 'amount']
        widgets = {
            'investor': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control text-right', 'placeholder': '0.00'}),
        }

CommittedCapitalFormSet = modelformset_factory(CommittedCapital, form=CommittedCapitalForm, extra=1, can_delete=True)

class CapitalCallForm(forms.ModelForm):
    class Meta:
        model = CapitalCall
        fields = ['date', 'call_type', 'amount']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['call_type'].queryset = CallType.objects.all()

CapitalCallFormSet = modelformset_factory(
    CapitalCall,
    form=CapitalCallForm,
    extra=1,
    can_delete=True
)