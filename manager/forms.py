from django import forms
from . models import Investor, Fund, Investment, CommittedCapital, Contact

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
        fields = ['company','fund','instrument','committed_amount','invested_amount']

class CommittedCapitalForm(forms.ModelForm):
    class Meta:
        model = CommittedCapital
        fields= ['fund','investor','amount','fund_interest']

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields= ['name','surname','phone_number','email_address', 'investor']
