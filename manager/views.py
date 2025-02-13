from django.http import HttpResponse
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.db.models import Sum, Max
from django.views.generic import View, ListView, DetailView, CreateView, UpdateView, DeleteView , TemplateView, FormView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.viewsets import ModelViewSet
from .filters import FundFilter
from .pagination import DefaultPagination
from .models import * 
from .serializers import *
from .forms import *
import requests
import json
from decimal import Decimal
import pandas as pd
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import transaction
from collections import defaultdict
from django.forms import formset_factory

# API Views
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

#HTML Template Views
class HomePageView(TemplateView):
    template_name = 'index.html'
    extra_context = {
        'title': 'LEMO Fund Manager Home',
    }

#Model List and Detail Views
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

        investor_data = defaultdict(lambda: {"total_commitment": 0, "dates": {}})
        total_commitments_by_date = defaultdict(lambda: 0)
        unique_dates = set()

        # 1️⃣ Get committed capital grouped by investor & date
        investor_commitments_by_date = (
            CommittedCapital.objects
            .filter(fund=fund)
            .values('investor', 'date')
            .annotate(investor_close_amount=Sum('amount'))
            .order_by('date')
        )

        unique_dates = set()
        for record in investor_commitments_by_date:
            investor_id = record['investor']
            date = record['date']
            committed_on_date = record['investor_close_amount']
            investor_data[investor_id]["dates"][date] = committed_on_date
            total_commitments_by_date[date] += committed_on_date
            unique_dates.add(date)

        # 2️⃣ Get total committed capital per investor
        committed_capital = (
            CommittedCapital.objects
            .filter(fund=fund)
            .values('investor')
            .annotate(total_commitment=Sum('amount'))
        )

        for record in committed_capital:
            investor_id = record["investor"]
            investor_data[investor_id]["total_commitment"] = record["total_commitment"]

        # 3️⃣ Get total committed capital for the entire fund
        total_committed_capital = (
            CommittedCapital.objects
            .filter(fund=fund)
            .aggregate(total_committed=Sum('amount'))
            .get('total_committed', 0) or 0
        )

        # 4️⃣ Get drawn capital per investor and total drawn capital
        drawn_capital = (
            CapitalCall.objects
            .filter(fund=fund)
            .values('investor')
            .annotate(investor_drawn_capital=Sum('amount'))
        )

        investor_drawn_capital_map = {item['investor']: item['investor_drawn_capital'] for item in drawn_capital}

        total_drawn_capital = (
            CapitalCall.objects
            .filter(fund=fund)
            .aggregate(total_drawn=Sum('amount'))
            .get('total_drawn', 0) or 0
        )

        # 5️⃣ Compute undrawn capital
        undrawn_committed_capital = total_committed_capital - total_drawn_capital

        # 6️⃣ Initialize variables for fund-wide totals
        total_capital_calls = total_distributions = total_operating_income = 0
        total_operating_expenses = total_unrealised_gains_or_losses = total_net_asset_value = 0
        total_fund_interest_committed = total_fund_interest_called = 0

        # 7️⃣ Process investor-level calculations
        investors_data = []

        for investor_id, data in investor_data.items():
            investor = Investor.objects.get(id=investor_id)
            committed_amount = data["total_commitment"]
            investor_capital_calls = investor_drawn_capital_map.get(investor_id, 0)

            investor_distributions = Distribution.objects.filter(fund=fund, investor=investor).aggregate(total_distributed=Sum('amount'))['total_distributed'] or 0
            investor_operating_income = OperatingIncome.objects.filter(fund=fund, investor=investor).aggregate(total_income=Sum('amount'))['total_income'] or 0
            investor_operating_expenses = OperatingExpense.objects.filter(fund=fund, investor=investor).aggregate(total_expenses=Sum('amount'))['total_expenses'] or 0                   
            investor_unrealised_gains = UnrealisedGains.objects.filter(fund=fund, investor=investor).aggregate(total_unrealised_gains=Sum('amount'))['total_unrealised_gains'] or 0                   
            investor_unrealised_losses = UnrealisedLosses.objects.filter(fund=fund, investor=investor).aggregate(total_unrealised_losses=Sum('amount'))['total_unrealised_losses'] or 0                   

            investor_unrealised_gains_or_losses = investor_unrealised_gains - investor_unrealised_losses

            # Update fund-wide totals
            total_capital_calls += investor_capital_calls
            total_distributions += investor_distributions
            total_operating_income += investor_operating_income
            total_operating_expenses += investor_operating_expenses
            total_unrealised_gains_or_losses += investor_unrealised_gains_or_losses

            investor_net_asset_value = (
                investor_capital_calls - investor_distributions +
                investor_operating_income - investor_operating_expenses +
                investor_unrealised_gains_or_losses
            )
            total_net_asset_value += investor_net_asset_value

            # Calculate Fund interest based on committed capital
            fund_interest_committed = (
                committed_amount / total_committed_capital if total_committed_capital > 0 else 0
            )

            # Calculate Fund interest based on called capital
            fund_interest_called = (
                investor_capital_calls / total_drawn_capital if total_drawn_capital > 0 else 0
            )

            total_fund_interest_committed += fund_interest_committed
            total_fund_interest_called += fund_interest_called

            # Append investor data
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
                'commitments_by_date': data["dates"],  # Store commitments grouped by date
            })

        # 8️⃣ Update context with all computed data
        context.update({
            'investors_data': investors_data,
            'unique_dates': unique_dates,
            'total_commitments_by_date': dict(total_commitments_by_date),
            'total_committed_capital': total_committed_capital,
            'total_drawn_capital': total_drawn_capital,
            'undrawn_committed_capital': undrawn_committed_capital,
            'total_capital_calls': total_capital_calls,
            'total_distributions': total_distributions,
            'total_operating_income': total_operating_income,
            'total_operating_expenses': total_operating_expenses,
            'total_unrealised_gains_or_losses': total_unrealised_gains_or_losses,
            'total_net_asset_value': total_net_asset_value,
            'total_fund_interest_committed': total_fund_interest_committed,
            'total_fund_interest_called': total_fund_interest_called,
        })

        return context

    #Functionality to export to Excel
    def get(self, request, *args, **kwargs):
        if request.GET.get('export') == 'excel':
            return self.export_to_excel()
        return super().get(request, *args, **kwargs)

    def export_to_excel(self):
        fund = self.get_object()
        committed_capital = CommittedCapital.objects.filter(fund=fund).values('investor').annotate(investor_commitment=Sum('amount')).values('investor', 'investor_commitment')
        
        # Prepare data for the Excel file
        data = [
            {
                'Investor': Investor.objects.get(id=entry['investor']).name,
                'Committed Capital': entry['investor_commitment'],
            }
            for entry in committed_capital
        ]

        df = pd.DataFrame(data)

        # Create Excel response
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename=fund_{fund.id}_data.xlsx'

        # Export to Excel using openpyxl
        df.to_excel(response, index=False, engine='openpyxl')
        return response

class InvestorsList(ListView):
    model = Investor
    template_name = 'investors/investors.html'
    context_object_name = 'investors'

    def get_queryset(self):
        # Start with all investors
        queryset = super().get_queryset()

        # Check for a search query
        query = self.request.GET.get('q')
        if query:
            # Filter by multiple fields using Q objects
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(short_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Pull all primary contacts
        primary_contacts = Contact.objects.filter(primary_contact=True)
        # Annotate each investor with their primary contact
        investors_data = []
        for investor in context['investors']:
            primary_contact = primary_contacts.filter(investor = investor).first()
            investors_data.append({
                'investor': investor,
                'primary_contact': primary_contact
            })

        context['investors_data'] = investors_data
        context['search_query'] = self.request.GET.get('q', '')
        return context

class InvestorDetail(DetailView):
    model = Investor
    template_name = 'investors/investor_overview.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investor = self.object

        investor_contacts = Contact.objects.filter(investor = investor)
        primary_contact = Contact.objects.get(investor = investor, primary_contact = True)

        context.update({
            'investor_contacts': investor_contacts,
            'primary_contact': primary_contact,
        })

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

class CompanyDetail(DetailView):
    model = Investment
    template_name = 'companies/company_overview.html'
    context_object_name = 'company'

class Dashboard(TemplateView):
    model = Fund
    template_name = 'reports/dashboard.html'
#    context_object_name = 'summary_data'

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

class AddInvestor(FormView):
    form_class = InvestorForm
    template_name = 'investors/add_investor.html'
    success_url = reverse_lazy('investors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['contact_formset'] = ContactFormSet(self.request.POST)
        else:
            context['contact_formset'] = ContactFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']

        if contact_formset.is_valid():
            self.object = form.save()
            contact_formset.instance = self.object
            contact_formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form = form))

class EditInvestor(UpdateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'investors/edit_investor.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('investors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['contact_formset'] = ContactFormSet(self.request.POST, instance=self.object)
        else:
            context['contact_formset'] = ContactFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        if contact_formset.is_valid():
            self.object = form.save()
            contact_formset.instance = self.object
            contact_formset.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

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

class AddCompany(CreateView):
    template_name = 'companies/add_company.html'
    form_class = CompanyForm
    success_url = reverse_lazy('companies')

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class EditCompany(UpdateView):
    model = Company
    form_class = CompanyForm
    template_name = 'companies/edit_company.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('companies')

class DeleteCompany(DeleteView):
    model = Company
    pk_url_kwarg = 'pk'
    template_name = "companies/confirm_delete.html"
    success_url = reverse_lazy('companies')  

# Fund Close
class CommittedCapitalCreateView(FormView):
    form_class = CommittedCapitalFormSet
    template_name = 'funds/fund_close2.html'
    success_url = reverse_lazy('funds')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        committedCapital = CommittedCapital.objects.all()
       
        if self.request.POST:
            context['formset'] = CommittedCapitalFormSet(self.request.POST)
        else:
            context['formset'] = CommittedCapitalFormSet(queryset=committedCapital)

        context['fund'] = get_object_or_404(Fund, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            instances = formset.save(commit=False)
            fund = context['fund']
            for instance in instances:
                instance.fund = fund
                instance.save()

            # Handle summary data
            summary_data = self.request.POST.get('summary_data', '[]')
            print('Received Summary Data:', summary_data)  # Debugging statement

            try:
                data = json.loads(summary_data)
                for item in data:
                    date = item.get('date')
                    investor_name = item.get('investor')
                    amount = float(item.get('amount'))

                    # Find or create investor
                    investor, created = Investor.objects.get_or_create(name=investor_name)

                    # Save committed capital entry
                    CommittedCapital.objects.create(
                        fund=fund,
                        investor=investor,
                        amount=amount,
                        date = date
                    )                    
            except json.JSONDecodeError:
                print('Error decoding JSON data')  # Debugging statement

            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class CommittedCapitalDelete(View):
    def delete(self, request, *args, **kwargs):
        try:
            investorName = self.kwargs['id']
            print(investorName,'investorName')
            committed_capital = get_object_or_404(CommittedCapital, investor=investorName)

            committed_capital.delete()

            return JsonResponse({'status': 'success', 'message': 'Entry deleted successfully.'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


# Fund Close Simple Approach

class FundCloseView(FormView):
    template_name = "funds/fund_close2.html"

    def get(self, request, pk):
        fund = get_object_or_404(Fund, pk=pk)
        CommittedCapitalFormSet = formset_factory(CommittedCapitalForm, extra=1, can_delete=True)
        formset = CommittedCapitalFormSet()
        return render(request, self.template_name, {"fund": fund, "formset": formset})

    def post(self, request, pk):
        fund = get_object_or_404(Fund, pk=pk)
        CommittedCapitalFormSet = formset_factory(CommittedCapitalForm, extra=1, can_delete=True)
        formset = CommittedCapitalFormSet(request.POST)

        commitment_date = request.POST.get('commitment_date')

        if formset.is_valid():
            for form in formset:
                if form.cleaned_data:
                    committed_capital = form.save(commit=False)
                    committed_capital.fund = fund
                    committed_capital.date = commitment_date
                    committed_capital.save()

            return redirect("fund_close", pk=fund.pk)
        
        else:
            for form in formset:
                print(formset.errors)  # If there are errors, print them
            return render(request, self.template_name, {"fund": fund, "formset": formset})

# Using Json for committed capital
class CommittedCapitalSubmitView(View):
    def get(self, request, *args, **kwargs):
        try:
            fund = get_object_or_404(Fund, pk=self.kwargs['pk'])
            committed_capitals = CommittedCapital.objects.filter(fund=fund)
            data = [
                {
                    "investor": commitment.investor.name,
                    "amount": commitment.amount,
                }
                for commitment in committed_capitals
            ]

            return JsonResponse(data, safe=False, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
    def delete(self, request, *args, **kwargs):
        try:
            investorName = self.kwargs['id']
            print(investorName,'investorName')
            committed_capital = get_object_or_404(CommittedCapital, investor=investorName)

            committed_capital.delete()

            return JsonResponse({'status': 'success', 'message': 'Entry deleted successfully.'}, status=200)

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    def post(self, request, *args, **kwargs):
        try:      
            data = json.loads(request.body)
            fund = get_object_or_404(Fund, pk=self.kwargs['pk'])

            # Process the submitted data
            for item in data:
                investor_name = item.get('investor')
                amount = float(item.get('amount'))

                # Retrieve existing investor or raise an error if not found
                try:
                    investor = Investor.objects.get(name=investor_name)
                except Investor.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Investor "{investor_name}" does not exist.'}, status=400)

                # Save committed capital entry
                CommittedCapital.objects.create(
                    fund=fund,
                    investor=investor,
                    amount=amount
                )

            return JsonResponse({'status': 'success'}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def generate_unique_number(fund):
    max_number = NoticeNumber.objects.filter(fund=fund).aggregate(Max('number'))['number__max']
    if max_number is not None:
        return max_number + 1
    else:
        return 1  # Start at 1 if there are no existing entries

class CapitalCallView(TemplateView, FormView):
    template_name = 'funds/capital_call.html'
    form_class = CapitalCallForm
    success_url = reverse_lazy('funds')    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund_id = self.kwargs['pk']
        fund = Fund.objects.get(id=fund_id)

        # Get commitment and called capital data for Fund
        committed_capitals = CommittedCapital.objects.filter(fund=fund)
        total_committed = committed_capitals.aggregate(Sum('amount'))['amount__sum']
        capital_calls = CapitalCall.objects.filter(fund=fund)
        total_drawn = capital_calls.values('investor').annotate(total_amount=Sum('amount'))

        formset = CapitalCallFormSet(queryset=CapitalCall.objects.none())

        # Calculate total drawn sum
        total_drawn_sum = sum([draw['total_amount'] for draw in total_drawn])

        # Calculate undrawn commitments
        total_undrawn_commitment = total_committed - total_drawn_sum if total_committed and total_drawn_sum else total_committed

        capital_accounts = []
        total_interests = 0

        for commitment in committed_capitals:
            drawn_amount = next((draw['total_amount'] for draw in total_drawn if draw['investor'] == commitment.investor.id), 0)
            undrawn_commitment = commitment.amount - drawn_amount
            fund_interest = (commitment.amount / total_committed) if total_committed else 0
            total_interests += fund_interest
            capital_accounts.append({
                'investor': commitment.investor,
                'commitment': commitment.amount,
                'drawn_amount': drawn_amount,
                'undrawn_commitment': undrawn_commitment,
                'fund_interest': fund_interest,
            })

        context.update({
            'formset': formset,
            'fund': fund,
            'total_committed': total_committed,
            'total_drawn_sum': total_drawn_sum,
            'total_interests': total_interests,
            'total_undrawn_commitment': total_undrawn_commitment,
            'capital_accounts': capital_accounts,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        fund_id = self.kwargs['pk']
        fund = Fund.objects.get(id=fund_id)
        formset = CapitalCallFormSet(request.POST)

        if formset.is_valid():
            print("Formset is valid")
            # Generate the notice number based on the last record for the fund
            last_notice_number = CapitalCall.objects.filter(fund=fund).order_by('notice_number').last()
            new_notice_number = (last_notice_number.notice_number + 1) if last_notice_number else 1
            notice_date = formset.forms[0].cleaned_data['date']  # Use the date from the first form

            for form in formset:
                form.cleaned_data['date'] = notice_date
                if form.cleaned_data:
                    call_type = form.cleaned_data['call_type']
                    amount = form.cleaned_data['amount']

                    committed_capitals = CommittedCapital.objects.filter(fund=fund)
                    total_committed = committed_capitals.aggregate(Sum('amount'))['amount__sum']

            for commitment in committed_capitals:
                if call_type.name in ['Management Fees', 'Advisory Fees']:
                    capital_call_amount = commitment.amount * fund.man_fee / 4
                else:
                    capital_call_amount = (commitment.amount / total_committed) * amount

                CapitalCall.objects.create(
                    notice_number=new_notice_number,
                    date=notice_date,
                    fund=fund,
                    investor=commitment.investor,
                    call_type=call_type,
                    amount=capital_call_amount
                )

            return redirect(reverse('capital_call', kwargs={'pk': fund.id}))
        else:
            print("Formset errors", formset.errors)
        # If the formset is not valid, re-render the page with errors
        return self.render_to_response(self.get_context_data(formset=formset))

class CapitalCallCreateView(FormView):
    form_class = CapitalCallFormSet
    template_name = 'funds/capital_call.html'
    success_url = reverse_lazy('funds')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = CapitalCallFormSet(self.request.POST, queryset=CapitalCall.objects.none())
        else:
            context['formset'] = CapitalCallFormSet(queryset=CapitalCall.objects.none())
        context['fund'] = get_object_or_404(Fund, pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            instances = formset.save(commit=False)
            fund = context['fund']
            for instance in instances:
                instance.fund = fund
                instance.save()
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class FormSuccessView(TemplateView):
    template_name = 'form_success.html'
    extra_context = {
        'title': 'Form Submitted',
        'heading': 'Success',
        'content': 'Record has been created.'
    }

