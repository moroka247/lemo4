from django.forms import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.urls import reverse_lazy
from django.db.models import Sum
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView , TemplateView
from django.views.generic.edit import FormView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from .filters import FundFilter
from .pagination import DefaultPagination
from .models import * 
from .serializers import *
from .forms import *
import requests
from decimal import Decimal


class CurrencyViewSet(ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

class CountryViewSet(ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    pagination_class = DefaultPagination    

class FundViewSet(ModelViewSet):
    queryset = Fund.objects.all()
    serializer_class = FundSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = FundFilter
    search_fields = ['name', 'short_name']

class InvestorViewSet(ModelViewSet):
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'short_name', 'reg_no']
    Ordering_fields = ['name']
    
class ContactListViewSet(ModelViewSet):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    pagination_class = DefaultPagination

class InvestorDocumentsViewSet(ModelViewSet):
    queryset = InvestorDocument.objects.all()
    serializer_class = InvestorDocumentsSerializer

class FundStructuresViewSet(ModelViewSet):
    queryset = FundStructure.objects.all()
    serializer_class = FundStructureSerializer

class InvestorTypesViewSet(ModelViewSet):
    queryset = InvestorType.objects.all()
    serializer_class = InvestorTypeSerializer

class FundCloseViewSet(ModelViewSet):
    queryset = FundClose.objects.all()
    serializer_class = FundCloseSerializer

class CommittedCapitalViewSet(ModelViewSet):
    queryset = CommittedCapital.objects.all()
    serializer_class = CommittedCapitalSerializer

class CallTypeViewSet(ModelViewSet):
    queryset = CallType.objects.all()
    serializer_class = CallTypeSerializer

class DistributionTypeViewSet(ModelViewSet):
    queryset = DistributionType.objects.all()
    serializer_class = DistributionTypeSerializer

class CapitalCallViewSet(ModelViewSet):
    queryset = CapitalCall.objects.all()
    serializer_class = CapitalCallSerializer

class DistributionViewSet(ModelViewSet):
    queryset = Distribution.objects.all()
    serializer_class = DistributionSerializer

class IndustryViewSet(ModelViewSet):
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer

class InstrumentViewSet(ModelViewSet):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer

class CompanyViewSet(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    pagination_class = DefaultPagination

class InvestmentViewSet(ModelViewSet):
    queryset = Investment.objects.all()
    serializer_class = InvestmentSerializer
    pagination_class = DefaultPagination

class DisbursementViewSet(ModelViewSet):
    queryset = Disbursement.objects.all()
    serializer_class = DisbursementSerializer

class HomePageView(TemplateView):
    template_name = 'index.html'
    extra_context = {
        'title': 'LEMO Fund Manager Home',
    }

class FundsList(ListView):
    model = Fund
    template_name = 'funds/funds.html'
    context_object_name = 'funds'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        funds = Fund.objects.all()
        funds_data =[]

        for fund in funds:

            #Retrieve capital commitments
            committed_capital = CommittedCapital.objects.filter(fund = fund).aggregate(total=Sum('amount'))['total'] or 0

            #Retrieve drawn capital records
            called_capital = CapitalCall.objects.filter(fund = fund).aggregate(total=Sum('amount'))['total'] or 0

            #Calculate the undrawn commitment
            undrawn_commitment = committed_capital - called_capital

            #Append Fund data record
            funds_data.append({
                'fund': fund,
                'committed_capital': committed_capital,
                'called_capital': called_capital,
                'undrawn_commitment': undrawn_commitment
            })

        #Pass the structured data to the template
        context['funds_data'] = funds_data
        return context

class FundDetail(DetailView):
    model = Fund
    template_name = 'funds/fund_overview.html'
    context_object_name = 'fund'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund = self.object

        # Calculate committed capital
        committed_capital = CommittedCapital.objects.filter(fund=fund).values('investor').annotate(investor_commitment=Sum('amount')).values('investor','investor_commitment')
        total_committed_capital = CommittedCapital.objects.filter(fund=fund).aggregate(total_committed=Sum('amount'))['total_committed'] or 0

        # Calculate drawn capital
        drawn_capital = CapitalCall.objects.filter(fund=fund).values('investor').annotate(investor_drawn_capital=Sum('amount'))
        total_drawn_capital = CapitalCall.objects.filter(fund=fund).aggregate(total_drawn=Sum('amount'))['total_drawn'] or 0

        # Calculate undrawn capital
        undrawn_committed_capital = total_committed_capital - total_drawn_capital

        # Initialize variables
        investors_data = []

        total_capital_calls = 0
        total_distributions = 0
        total_operating_income = 0
        total_operating_expenses = 0
        total_unrealised_gains_or_losses = 0
        total_net_asset_value = 0
        total_fund_interest_committed = 0
        total_fund_interest_called = 0

        for invested in committed_capital:
            investor = Investor.objects.get(id = invested['investor'])
            committed_amount = invested['investor_commitment']

            investor_capital_calls = CapitalCall.objects.filter(fund=fund, investor=investor).aggregate(total_called=Sum('amount'))['total_called'] or 0
            investor_distributions = Distribution.objects.filter(fund=fund, investor=investor).aggregate(total_distributted=Sum('amount'))['total_distributted'] or 0
            investor_operating_income = OperatingIncome.objects.filter(fund=fund, investor=investor).aggregate(total_income=Sum('amount'))['total_income'] or 0
            investor_operating_expenses = OperatingExpense.objects.filter(fund=fund, investor=investor).aggregate(total_expenses=Sum('amount'))['total_expenses'] or 0                   
            investor_unrealised_gains = UnrealisedGains.objects.filter(fund=fund, investor=investor).aggregate(total_unrealised_gains=Sum('amount'))['total_unrealised_gains'] or 0                   
            investor_unrealised_losses = UnrealisedLosses.objects.filter(fund=fund, investor=investor).aggregate(total_unrealised_losses=Sum('amount'))['total_unrealised_losses'] or 0                   

            investor_unrealised_gains_or_losses = investor_unrealised_gains - investor_unrealised_losses

            total_capital_calls += investor_capital_calls
            total_distributions += investor_distributions
            total_operating_income += investor_operating_income
            total_operating_expenses += investor_operating_expenses
            total_unrealised_gains_or_losses += investor_unrealised_gains_or_losses

            investor_net_asset_value = investor_capital_calls - investor_distributions + investor_operating_income + investor_operating_expenses + investor_unrealised_gains_or_losses
            total_net_asset_value += investor_net_asset_value

            # Calculate Fund interest based on committed capital
            if total_committed_capital > 0:
                fund_interest_committed = committed_amount / total_committed_capital
            else:
                fund_interest_committed = 0

            # Calculate Fund interest based on called capital
            if total_drawn_capital > 0:
                fund_interest_called = investor_capital_calls / total_drawn_capital
            else:
                fund_interest_called = 0 

            total_fund_interest_committed += fund_interest_committed
            total_fund_interest_called += fund_interest_called

            # Add to context dataset
            investors_data.append({
                'investor': investor,
                'committed_amount': committed_amount,
                'investor_capital_calls': investor_capital_calls,
                'investor_distributions': investor_distributions,
                'investor_operating_income': investor_operating_income,
                'investor_operating_expenses': investor_operating_expenses,
                'investor_unrealised_gains_or_losses': investor_unrealised_gains_or_losses,
                'investor_net_asset_value': investor_net_asset_value,
                'fund_interest_committed': fund_interest_committed,
                'fund_interest_called': fund_interest_called,
            })

        context.update({
            'investors_data': investors_data,
            'total_committed_capital': total_committed_capital,
            'total_drawn_capital': total_drawn_capital,
            'undrawn_committed_capital': undrawn_committed_capital,
            'total_capital_calls': total_capital_calls,
            'total_distributions': total_distributions,
            'total_operating_income': total_operating_income,
            'total_operating_expenses': total_operating_expenses,
            'total_unrealosed_gains_or_losses': total_unrealised_gains_or_losses,
            'total_net_asset_value': total_net_asset_value,
            'total_fund_interest_committed': total_fund_interest_committed,
            'total_fund_interest_called': total_fund_interest_called,
        })
        return context

class InvestorsList(ListView):
    model = Investor
    template_name = 'investors/investors.html'
    context_object_name = 'investors'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        primary_contacts = Contact.objects.filter(main_contact=True)
        # Annotate each investor with their primary contact
        investors_data = []
        for investor in context['investors']:
            primary_contact = primary_contacts.filter(investor = investor).first()
            investors_data.append({
                'investor': investor,
                'primary_contact': primary_contact
            })
        context['investors_data'] = investors_data
        return context

class InvestorDetail(DetailView):
    model = Investor
    template_name = 'investors/investor_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        selected_investor = self.object
        context['contacts'] = Contact.objects.filter(investor = selected_investor)
        return context

class InvesmentsList(ListView):
    model = Investment
    template_name = 'investments/investments.html'
    context_object_name = 'investments'

class InvestmentDetail(DetailView):
    model = Investment
    template_name = 'investments/investment_overview.html'
    context_object_name = 'investment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        return context

class ContactsList(ListView):
    model = Contact
    template_name = 'contacts/contacts.html'
    context_object_name = 'contacts'

class CompaniesList(ListView):
    model = Company
    template_name = 'companies/companies.html'
    context_object_name = 'companies'

# CRUD Views
class AddFund(CreateView):
    model = Fund
    form_class = FundForm
    template_name = 'funds/add_fund.html'
    context_object_name = 'fund'
    success_url = reverse_lazy('funds')

    def form_valid(self, form):
        return super().form_valid(form)

class EditFund(UpdateView):
    model = Fund
    form_class = FundForm
    template_name = 'funds/edit_fund.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('funds')

class DeleteFund(DeleteView):
    model = Fund
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('funds')
    template_name = "funds/confirm_delete.html"

class AddInvestor(CreateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'investors/add_investor.html'
    success_url = reverse_lazy('investors')

    def form_valid(self, form):
        return super().form_valid(form)

class EditInvestor(UpdateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'investors/edit_investor.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('investors')

class DeleteInvestor(DeleteView):
    model = Investor
    pk_url_kwarg = 'pk'
    template_name = "investors/confirm_delete.html"
    success_url = reverse_lazy('investors')

class AddInvestment(CreateView):
    template_name = 'investments/add_investment.html'
    form_class = InvestmentForm
    success_url = reverse_lazy('investments')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class EditInvestment(UpdateView):
    model = Investment
    form_class = InvestmentForm
    template_name = 'investments/edit_investment.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('investments')

class DeleteInvestment(DeleteView):
    model = Investment
    pk_url_kwarg = 'pk'
    template_name = "investments/confirm_delete.html"
    success_url = reverse_lazy('investments')

class AddContact(CreateView):
    template_name = 'contacts/add_contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contacts')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class EditContact(UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = 'contacts/edit_contact.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('contacts')

class DeleteContact(DeleteView):
    model = Contact
    pk_url_kwarg = 'pk'
    template_name = "contacts/confirm_delete.html"
    success_url = reverse_lazy('contacts')

class FormSuccessView(TemplateView):
    template_name = 'form_success.html'
    extra_context = {
        'title': 'Form Submitted',
        'heading': 'Success',
        'content': 'Record has been created.'
    }

def process_drawdown(request):
    notices_count = NoticeNumber.objects.count()
    new_number = notices_count + 1

    NoticeNumber.number = new_number
    NoticeNumber.save()

  
