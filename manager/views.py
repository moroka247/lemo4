from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.shortcuts import render
from django.urls import reverse_lazy
from django.db.models import Sum, Max
from django.db.models.functions import ExtractYear, ExtractMonth
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
from decimal import Decimal, InvalidOperation
import pandas as pd
from django.db.models import Prefetch, Count, Sum, Max, F, Q
from django.core.paginator import Paginator
from django.shortcuts import render
from django.db import IntegrityError, transaction
from collections import defaultdict
from django.forms import formset_factory
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from .utils import xirr
import calendar
from .choices import FeeBasis

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

class NetAssetValueViewSet(ModelViewSet):
    queryset = NetAssetValue.objects.all()
    serializer_class = NetAssetValueSerializer

class InvesotContactViewSet(ModelViewSet):
    queryset = InvestorContact.objects.all()
    serializer_class = InvestorContactSerializer

class AllocationRuleViewSet(ModelViewSet):
    queryset = AllocationRule.objects.all()
    serializer_class = AllocationRuleSerializer

class FundParameterViewSet(ModelViewSet):
    queryset = FundParameter.objects.all()
    serializer_class = FundParameterSerializer

# Home Page and Authentication

class HomePageView(TemplateView):
    template_name = 'index.html'
    extra_context = {
        'title': 'LEMO Fund Manager Home',
    }

class Dashboard(TemplateView):
    model = Fund
    template_name = 'reports/dashboard.html'

class CustomRegisterView(FormView):
    template_name = 'authentication/register.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('dashboard')

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('login')

class FormSuccessView(TemplateView):
    template_name = 'form_success.html'
    extra_context = {
        'title': 'Form Submitted',
        'heading': 'Success',
        'content': 'Record has been created.'
    }


# Funds Administration

class FundsList(LoginRequiredMixin, ListView):
    model = Fund
    template_name = 'funds/funds2.html'
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

            #Retrieve distribution records
            distributions = Distribution.objects.filter(fund = fund).aggregate(total=Sum('amount'))['total'] or 0

            #Append Fund data record
            funds_data.append({
                'fund': fund,
                'committed_capital': committed_capital,
                'called_capital': called_capital,
                'undrawn_commitment': undrawn_commitment,
                'distributions': distributions,
            })

            # Calculate totals for summary
            total_committed = sum(item['committed_capital'] for item in funds_data)
            total_called = sum(item['called_capital'] for item in funds_data)

            context['total_committed'] = total_committed
            context['total_called'] = total_called

        #Pass the structured data to the template
        context['funds_data'] = funds_data
        return context

class FundDetail(DetailView):
    model = Fund
    template_name = 'funds/fund_overview4.html'
    context_object_name = 'fund'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund = self.object

        # Get date range from request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Parse date strings to actual date objects
        start_date = parse_date(start_date) if start_date else None
        end_date = parse_date(end_date) if end_date else None

        # Apply date filtering only if both dates are provided
        date_filter = {}
        if start_date and end_date:
            date_filter['date__range'] = (start_date, end_date)

        investor_data = defaultdict(lambda: {"total_commitment": 0, "dates": {}})
        total_commitments_by_date = defaultdict(lambda: 0)
        unique_dates = set()

        # Get committed capital grouped by investor & date
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

        # Get total committed capital per investor
        committed_capital = (
            CommittedCapital.objects
            .filter(fund=fund)
            .values('investor')
            .annotate(total_commitment=Sum('amount'))
        )

        for record in committed_capital:
            investor_id = record["investor"]
            investor_data[investor_id]["total_commitment"] = record["total_commitment"]

        # Get total committed capital for the entire fund
        total_committed_capital = (
            CommittedCapital.objects
            .filter(fund=fund)
            .aggregate(total_committed=Sum('amount'))
            .get('total_committed', 0) or 0
        )

        # Get drawn capital per investor and total drawn capital
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

        # Compute undrawn capital
        undrawn_committed_capital = total_committed_capital - total_drawn_capital

        # PORTFOLIO INVESTMENTS


        # Fetch investments grouped by company
        investments_by_company = defaultdict(list)

        investments = Investment.objects.filter(fund=fund).select_related('company', 'instrument')

        for inv in investments:
            investments_by_company[inv.company.name].append({
                "instrument": inv.instrument.name,
                "committed_amount": inv.committed_amount,
                "invested_amount": inv.invested_amount,
                "realised_proceeds": inv.realised_proceeds,
                "valuation": inv.valuation,
                "IRR": "-",  # Placeholder
                "MOIC": "-",  # Placeholder
            })

        # PERFORMACE / CASH FLOWS

        # Get distinct types for column headers
        call_types = list(CallType.objects.values_list('name', flat=True))
        distribution_types = list(DistributionType.objects.values_list('name', flat=True))

        # Fetch Capital Calls grouped by date, notice_number, and call_type
        capital_calls_by_type_n_date = (
            CapitalCall.objects
            .filter(fund=fund, **date_filter)
            .values('date', 'notice_number', 'call_type__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('date', 'notice_number', 'call_type__name')
        )

        # Fetch Distributions grouped by date, notice_number, and distribution_type
        distributions_by_type_n_date = (
            Distribution.objects
            .filter(fund=fund, **date_filter)
            .values('date', 'notice_number', 'distribution_type__name')
            .annotate(total_amount=Sum('amount'))
            .order_by('date', 'notice_number', 'distribution_type__name')
        )

        # Unified structure: { (date, notice_number): { "capital_calls": {...}, "distributions": {...} } }
        calls_n_distributions_table_data = defaultdict(lambda: {
            "capital_calls": {ct: 0 for ct in call_types},
            "distributions": {dt: 0 for dt in distribution_types}
        })

        # Populate Capital Calls
        for call in capital_calls_by_type_n_date:
            key = (call['date'], call['notice_number'])
            calls_n_distributions_table_data[key]["capital_calls"][call['call_type__name']] = call['total_amount']

        # Populate Distributions
        for distribution in distributions_by_type_n_date:
            key = (distribution['date'], distribution['notice_number'])
            calls_n_distributions_table_data[key]["distributions"][distribution['distribution_type__name']] = distribution['total_amount']

        # Convert dictionary to a sorted list for template rendering
        calls_n_distributions_table_rows = [
            (date, notice_number, data) for (date, notice_number), data in sorted(calls_n_distributions_table_data.items())
        ]

         # Calculate net cash flows
        for (date, notice_number), data in calls_n_distributions_table_data.items():
            total_calls = sum(data['capital_calls'].values())  # Sum all capital calls and make them negative
            total_distributions = sum(data['distributions'].values())  # Sum all distributions
            net_cash_flow = total_distributions - total_calls  # Net Cash Flow
            data['net_cash_flow'] = net_cash_flow  # Store the net cash flow in the dictionary


        # Fetch the highest NAV within the date range
        highest_nav_entry = (
            NetAssetValue.objects
            .filter(fund=fund, **date_filter)
            .aggregate(highest_nav=Max('amount'))
        )
        highest_nav = highest_nav_entry['highest_nav'] if highest_nav_entry['highest_nav'] else None

        # Determine the latest available date for NAV
        latest_cashflow_date = max([date for date, _ in calls_n_distributions_table_data.keys()], default=None)

        # Fetch the last notice number in the dataset

        try:
            last_notice_number = max(
                [notice_number for _, notice_number in calls_n_distributions_table_data.keys() if notice_number is not None], 
                default=0
            ) + 1 # Increment to keep it unique
        except (ValueError, TypeError):
            last_notice_number = 1  # Fallback value

        # Add highest NAV as a final cash flow
        if highest_nav and latest_cashflow_date:
            calls_n_distributions_table_data[(latest_cashflow_date, last_notice_number)] = {
                "capital_calls": {ct: 0 for ct in call_types},
                "distributions": {dt: 0 for dt in distribution_types},
                "net_cash_flow": highest_nav
            }

        # Convert updated dictionary to a sorted list
        calls_n_distributions_table_rows = [
            (date, notice_number, data) for (date, notice_number), data in sorted(calls_n_distributions_table_data.items())
        ]

        # Fetch the cashflows, which should be a list of tuples (date, cashflow_value)
        cashflows = sorted(
            [(date, data['net_cash_flow']) for (date, _), data in calls_n_distributions_table_data.items()]
        )

        # Compute XIRR
        if any(cf[1] > 0 for cf in cashflows) and any(cf[1] < 0 for cf in cashflows):
            net_xirr = xirr(cashflows)  # Use the imported xirr function
        else:
            net_xirr = None

        # Initialize variables for fund-wide totals
        total_capital_calls = total_distributions = total_operating_income = 0
        total_operating_expenses = total_unrealised_gains_or_losses = total_net_asset_value = 0
        total_fund_interest_committed = total_fund_interest_called =  net_times_money = 0
       
        # Process investor-level calculations
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

            net_times_money = total_distributions / total_drawn_capital if total_drawn_capital != 0 else 0


            # Get the period parameter from the request
        period = self.request.GET.get('period', 'quarterly')
        
        # Get capital calls and distributions data
        capital_calls_data = self.get_capital_data(fund, 'call', period)
        distributions_data = self.get_capital_data(fund, 'distribution', period)
        
        # Prepare data for the chart (using the same format as your working example)
        labels, calls_values, dist_values = self.prepare_simple_chart_data(
            capital_calls_data, distributions_data, period
        )

        # Update context with all computed data
        context.update({
            'investors_data': investors_data,
            'investments_by_company': dict(investments_by_company),
            'unique_dates': unique_dates,
            'calls_n_distributions_table_data': calls_n_distributions_table_data,
            'calls_n_distributions_table_rows': calls_n_distributions_table_rows,
            'latest_cashflow_date': latest_cashflow_date,
            'highest_nav': highest_nav,
            'call_types': call_types,
            'distribution_types': distribution_types,
            'net_xirr': net_xirr,
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
            'net_times_money': net_times_money,
            'capital_calls_data': capital_calls_data,
            'distributions_data': distributions_data,
            'chart_labels': labels,
            'chart_calls_data': calls_values,
            'chart_dist_data': dist_values,
            'selected_period': period,
        })

        return context

    # Charts Functionality
    def get_capital_data(self, fund, data_type, period):
        """
        Get capital calls or distributions data
        """
        if data_type == 'call':
            queryset = CapitalCall.objects.filter(fund=fund)
        else:
            queryset = Distribution.objects.filter(fund=fund)
        
        # If no data, return empty list
        if not queryset.exists():
            return []
        
        # For simplicity, let's just get the total amounts by year
        # You can enhance this later with proper period grouping
        yearly_data = list(queryset.annotate(
            year=ExtractYear('date')
        ).values('year').annotate(total=Sum('amount')).order_by('year'))
        
        return yearly_data

    def prepare_simple_chart_data(self, calls_data, dist_data, period):
        """
        Prepare simple data for the chart in the same format as your working example
        """
        # If no data, return some sample data for testing
        if not calls_data and not dist_data:
            # Sample data for testing
            if period == 'quarterly':
                return ['Q1', 'Q2', 'Q3', 'Q4'], [120, 150, 180, 200], [80, 120, 160, 220]
            else:
                return ['2023', '2024'], [100000, 150000], [80000, 120000]
        
        # Extract years from data
        years = set()
        for item in calls_data:
            years.add(item['year'])
        for item in dist_data:
            years.add(item['year'])
        
        # Sort years
        sorted_years = sorted(years)
        
        # Create data arrays
        calls_values = [0] * len(sorted_years)
        dist_values = [0] * len(sorted_years)
        
        # Fill calls data
        for item in calls_data:
            idx = sorted_years.index(item['year'])
            calls_values[idx] = float(item['total'])
        
        # Fill distributions data
        for item in dist_data:
            idx = sorted_years.index(item['year'])
            dist_values[idx] = float(item['total'])
        
        # Format labels based on period
        if period == 'quarterly':
            # For quarterly view, we'll just use Q1, Q2, Q3, Q4 as placeholders
            # You can enhance this later to show actual quarters
            labels = ['Q1', 'Q2', 'Q3', 'Q4']
            # Use only the first 4 data points for the quarterly view
            calls_values = calls_values[:4] if len(calls_values) >= 4 else calls_values + [0] * (4 - len(calls_values))
            dist_values = dist_values[:4] if len(dist_values) >= 4 else dist_values + [0] * (4 - len(dist_values))
        else:
            # For yearly view, use the years as labels
            labels = [str(year) for year in sorted_years]
        
        return labels, calls_values, dist_values


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

class CapitalCallView(TemplateView):
    template_name = "funds/capital_call.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund_id = self.kwargs['pk']
        fund = get_object_or_404(Fund, pk=fund_id)
        
        # Get all investors with commitments to this fund
        investor_data = []
        total_drawn = Decimal('0')
        
        # Get committed capital data
        commitments = CommittedCapital.objects.filter(fund=fund)
        investor_commitments = commitments.values('investor').annotate(
            total_committed=Sum('amount')
        )
        
        # Get total commitments to the Fund
        total_committed = commitments.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate total committed and prepare investor data
        for item in investor_commitments:
            investor = Investor.objects.get(id=item['investor'])
            committed_amount = item['total_committed'] or Decimal('0')
            
            # Calculate fund interest
            fund_interest = Decimal('0')
            if total_committed > 0:
                fund_interest = committed_amount / total_committed
            
            investor_data.append({
                'investor': investor,
                'committed_amount': committed_amount,
                'fund_interest': fund_interest,
            })
        
        # Get capital drawn data for each investor
        capital_calls = CapitalCall.objects.filter(fund=fund)
        for investor_info in investor_data:
            investor_drawn = capital_calls.filter(
                investor=investor_info['investor']
            ).aggregate(total_drawn=Sum('amount'))['total_drawn'] or Decimal('0')
            
            investor_info['drawn_amount'] = investor_drawn
            investor_info['undrawn_amount'] = investor_info['committed_amount'] - investor_drawn
            total_drawn += investor_drawn
        
        # Get all capital call items grouped by notice number AND description
        notice_calls = {}
        for call in CapitalCall.objects.filter(fund=fund).select_related('notice_number', 'call_type', 'allocation_rule', 'investor'):
            notice_code = call.notice_number.notice_code if call.notice_number else 'No Notice'
            
            if notice_code not in notice_calls:
                notice_calls[notice_code] = {
                    'notice_number': call.notice_number,
                    'descriptions': {},
                    'total_amount': Decimal('0')
                }
            
            # Group by description within each notice
            description_key = f"{call.description}-{call.call_type.name}-{call.allocation_rule.name}"
            
            if description_key not in notice_calls[notice_code]['descriptions']:
                notice_calls[notice_code]['descriptions'][description_key] = {
                    'description': call.description,
                    'call_type': call.call_type,
                    'allocation_rule': call.allocation_rule,
                    'investor_amounts': {},
                    'total': Decimal('0')
                }
            
            # Store amount by investor
            notice_calls[notice_code]['descriptions'][description_key]['investor_amounts'][call.investor.id] = call.amount
            notice_calls[notice_code]['descriptions'][description_key]['total'] += call.amount
            notice_calls[notice_code]['total_amount'] += call.amount
        
        # Get unpaid management fees
        unpaid_management_fees = ManagementFees.objects.filter(
            fund=fund,
            paid=False,
            capital_call__isnull=True
        ).order_by('period_end_date')
        
        # Get management fee types for the form
        management_fee_call_type = CallType.objects.filter(name__icontains='management').first()
        
        # Forms and other context
        context['date_form'] = CapitalCallDateForm()
        context['item_formset'] = CapitalCallItemFormSet(prefix='capital_call_items')
        context['call_types'] = CallType.objects.all()
        context['allocation_rules'] = AllocationRule.objects.all()
        
        context.update({
            'fund': fund,
            'investor_data': investor_data,
            'notice_calls': notice_calls,
            'total_committed': total_committed,
            'total_drawn': total_drawn,
            'total_undrawn': total_committed - total_drawn,
            'unpaid_management_fees': unpaid_management_fees,
            'management_fee_call_type': management_fee_call_type,
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        fund = get_object_or_404(Fund, pk=self.kwargs['pk'])
        
        # Handle integrated capital call form
        item_formset = CapitalCallItemFormSet(
            request.POST, 
            prefix='capital_call_items'
        )
        
        if item_formset.is_valid():
            call_date_str = request.POST.get('call_date')
            due_date_str = request.POST.get('due_date')
            
            if not call_date_str or not due_date_str:
                messages.error(request, 'Please provide both call date and due date.')
                context = self.get_context_data()
                context['item_formset'] = item_formset
                return self.render_to_response(context)
            
            call_date = datetime.strptime(call_date_str, '%Y-%m-%d').date()
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            # Create a notice for this batch (notice_code will be auto-generated per fund)
            notice = NoticeNumber.objects.create(
                date=call_date,
                fund=fund,
                investor=None  # Batch notice
            )
            
            # Process management fees if any are selected (EXCLUDING General Partners)
            selected_fee_ids = request.POST.getlist('selected_management_fees')
            total_management_fees = Decimal('0')
            management_fee_capital_calls = []  # Store created capital calls for management fees
            
            for fee_id in selected_fee_ids:
                try:
                    management_fee = ManagementFees.objects.get(
                        id=fee_id,
                        fund=fund,
                        paid=False,
                        capital_call__isnull=True
                    )
                    
                    # Create capital calls for management fee and get the created capital calls
                    created_calls = self.create_management_fee_capital_call(fund, management_fee, notice, due_date)
                    
                    if created_calls:
                        # Link the management fee to the first capital call (they all reference the same fee)
                        management_fee.capital_call = created_calls[0]  # Link to first capital call
                        management_fee.save()
                        total_management_fees += management_fee.gross_fee_amount
                        management_fee_capital_calls.extend(created_calls)
                    
                except ManagementFees.DoesNotExist:
                    continue
            
            # Process regular capital call items (INCLUDING General Partners)
            for form in item_formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    call_type = form.cleaned_data['call_type']
                    allocation_rule = form.cleaned_data['allocation_rule']
                    description = form.cleaned_data['description']
                    total_amount = form.cleaned_data['amount']
                    
                    # Get investor commitments and totals (INCLUDING General Partners)
                    investor_commitments = CommittedCapital.objects.filter(fund=fund)
                    total_committed = investor_commitments.aggregate(
                        Sum('amount')
                    )['amount__sum'] or Decimal('0')
                    
                    # Get drawn amounts before this date (INCLUDING General Partners)
                    drawn_before = CapitalCall.objects.filter(
                        fund=fund, 
                        date__lt=call_date
                    ).values('investor').annotate(
                        total_drawn=Sum('amount')
                    )
                    drawn_dict = {item['investor']: item['total_drawn'] for item in drawn_before}
                    total_drawn_before = sum(drawn_dict.values(), Decimal('0'))
                    
                    # Create capital calls for each investor (INCLUDING General Partners)
                    for commitment in investor_commitments:
                        investor = commitment.investor
                        committed_amount = commitment.amount
                        drawn_amount = drawn_dict.get(investor.id, Decimal('0'))
                        
                        # Allocation logic
                        if allocation_rule.name == 'Committed Capital':
                            investor_share = (committed_amount / total_committed) * total_amount
                        elif allocation_rule.name == 'Undrawn Commitment':
                            undrawn_amount = committed_amount - drawn_amount
                            total_undrawn = total_committed - total_drawn_before
                            investor_share = (undrawn_amount / total_undrawn) * total_amount if total_undrawn > 0 else Decimal('0')
                        else:
                            investor_share = Decimal('0')
                        
                        if investor_share > 0:
                            CapitalCall.objects.create(
                                notice_number=notice,
                                fund=fund,
                                investor=investor,
                                date=call_date,
                                due_date=due_date,
                                call_type=call_type,
                                allocation_rule=allocation_rule,
                                description=description,
                                amount=investor_share
                            )
            
            # Success message
            if total_management_fees > 0:
                messages.success(
                    request, 
                    f'Capital call batch {notice.notice_code} created successfully! '
                    f'Including ${total_management_fees:,.2f} in management fees.'
                )
            else:
                messages.success(request, f'Capital call batch {notice.notice_code} created successfully!')
            
            return redirect('capital_call', pk=fund.pk)
        
        # If forms are invalid
        messages.error(request, 'Please correct the errors below.')
        context = self.get_context_data()
        context['item_formset'] = item_formset
        return self.render_to_response(context)

    def create_management_fee_capital_call(self, fund, management_fee, notice, due_date):
        """Create capital calls for a management fee across all investors (excluding General Partners) and return the created calls"""
        # Get management fee call type
        management_call_type = CallType.objects.filter(name__icontains='management').first()
        if not management_call_type:
            management_call_type = CallType.objects.create(
                name='Management Fee',
                description='Regular management fee charge'
            )
        
        # Get allocation rule (typically Committed Capital for management fees)
        allocation_rule = AllocationRule.objects.filter(name='Committed Capital').first()
        if not allocation_rule:
            allocation_rule = AllocationRule.objects.create(
                name='Committed Capital',
                description='Allocation based on committed capital percentage'
            )
        
        # Get total commitments for the fund, excluding General Partners (for management fees)
        try:
            gp_type = InvestorType.objects.get(category="General Partner")
            
            total_committed = CommittedCapital.objects.filter(fund=fund).exclude(
                investor__category=gp_type  # Exclude General Partners
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            
            # Get investor commitments, excluding General Partners (for management fees)
            investor_commitments = CommittedCapital.objects.filter(fund=fund).exclude(
                investor__category=gp_type  # Exclude General Partners
            )
            
        except InvestorType.DoesNotExist:
            # If General Partner type doesn't exist, include all investors
            total_committed = CommittedCapital.objects.filter(fund=fund).aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            
            investor_commitments = CommittedCapital.objects.filter(fund=fund)
        
        if total_committed == 0:
            return []
        
        created_calls = []
        
        # Use the total fee amount (including VAT if applicable)
        fee_amount_to_allocate = management_fee.total_fee_amount

        # Create capital calls for each investor (excluding General Partners for management fees only)
        for commitment in investor_commitments:
            investor = commitment.investor
            investor_share = (commitment.amount / total_committed) * fee_amount_to_allocate
            
            if investor_share > 0:
                capital_call = CapitalCall.objects.create(
                    notice_number=notice,
                    fund=fund,
                    investor=investor,
                    date=notice.date,
                    due_date=due_date,
                    call_type=management_call_type,
                    allocation_rule=allocation_rule,
                    description=f"Management Fee {management_fee.period_start_date} to {management_fee.period_end_date}",
                    amount=investor_share
                )
                created_calls.append(capital_call)
        
        return created_calls

class FundCloseView(DetailView):
    model = Fund
    template_name = "funds/fund_close.html"
    context_object_name = 'fund'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        fund = self.get_object()
        
        # Get investors with their cumulative commitments and latest date
        investor_data = []
        total_committed = 0

        commitments = CommittedCapital.objects.filter(fund=fund)
        
        # Calculate total committed
        total_committed = commitments.aggregate(Sum('amount'))['amount__sum'] or 0

        # Get distinct investors with their totals and latest dates
        investor_commitments = commitments.values('investor').annotate(
            total_amount=Sum('amount'),
            last_date=Max('date')
        ).order_by('investor__name')
        
        fund_interest = 0
        total_fund_interests = 0

        for item in investor_commitments:
            investor = Investor.objects.get(id=item['investor'])
            if total_committed > 0:
                fund_interest = (item['total_amount'] / total_committed) * 100
                total_fund_interests += fund_interest

            investor_data.append({
                'investor': investor,
                'investor_id': investor.id,
                'investor_name': investor.name,
                'total_amount': item['total_amount'],
                'last_date': item['last_date'],
                'fund_interest': fund_interest,
            })

        # Get investors without commitments to this fund
        committed_investor_ids = [item['investor_id'] for item in investor_data]
        available_investors = Investor.objects.exclude(
            id__in=committed_investor_ids
        ).order_by('name')
        
        # Calculate overall totals
        total_investors = len(investor_data)
        target_commitment = fund.target_commitment or 0
        remaining_target = max(target_commitment - total_committed, 0)
        progress_percentage = (total_committed / target_commitment * 100) if target_commitment else 0
        
        context.update({
            'investor_data': investor_data,
            'available_investors': available_investors,
            'total_committed': total_committed,
            'total_investors': total_investors,
            'remaining_target': remaining_target,
            'progress_percentage': progress_percentage,
            'target_commitment': target_commitment,
            'today': timezone.now().date(),
            'total_fund_interests': total_fund_interests,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        fund = self.object
        
        # Only handle batch commitments
        if 'add_commitments' in request.POST:
            # Handle multiple commitments
            date_str = request.POST.get('date')
            investor_ids = request.POST.getlist('investors')
            amounts = request.POST.getlist('amounts')
            
            if not date_str:
                messages.error(request, 'Please select a date.')
                return redirect('fund_close', pk=fund.pk)
            
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if date > timezone.now().date():
                    messages.error(request, 'Cannot add commitments for future dates.')
                    return redirect('fund_close', pk=fund.pk)
            except ValueError:
                messages.error(request, 'Invalid date format.')
                return redirect('fund_close', pk=fund.pk)
            
            success_count = 0
            errors = []
            
            for i, (investor_id, amount_str) in enumerate(zip(investor_ids, amounts)):
                if not investor_id or not amount_str:
                    continue  # Skip empty rows
                
                try:
                    investor = Investor.objects.get(id=investor_id)
                    amount = Decimal(amount_str)
                    
                    if amount <= 0:
                        errors.append(f"Row {i+1}: Amount must be greater than zero")
                        continue
                    
                    # Check if investor already has a commitment on this date
                    existing_commitment = CommittedCapital.objects.filter(
                        fund=fund,
                        investor=investor,
                        date=date
                    ).exists()
                    
                    if existing_commitment:
                        errors.append(f"Row {i+1}: {investor.name} already has a commitment on {date}")
                        continue
                    
                    # Create new commitment
                    CommittedCapital.objects.create(
                        fund=fund,
                        investor=investor,
                        date=date,
                        amount=amount
                    )
                    success_count += 1
                    
                except (Investor.DoesNotExist, ValueError, InvalidOperation) as e:
                    errors.append(f"Row {i+1}: Error processing commitment - {str(e)}")
                    continue
            
            if success_count > 0:
                messages.success(request, 
                    f'Successfully added {success_count} commitment(s) for {date}.')
            
            if errors:
                for error in errors:
                    messages.error(request, error)
            
            if success_count == 0 and not errors:
                messages.warning(request, 'No commitments were added. Please check your inputs.')
        
        return redirect('fund_close', pk=fund.pk)

class InvestorCommitmentsView(LoginRequiredMixin, ListView):
    template_name = "funds/investor_commitments.html"
    context_object_name = 'commitments'
    
    def get_queryset(self):
        self.fund = get_object_or_404(Fund, pk=self.kwargs['fund_pk'])
        self.investor = get_object_or_404(Investor, pk=self.kwargs['investor_pk'])
        return CommittedCapital.objects.filter(
            fund=self.fund, 
            investor=self.investor
        ).order_by('-date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fund'] = self.fund
        context['investor'] = self.investor
        
        # Calculate total commitment
        total_commitment = self.get_queryset().aggregate(Sum('amount'))['amount__sum'] or 0
        context['total_commitment'] = total_commitment
        
        # Add form for new commitment (pre-select the investor)
        context['commitment_form'] = CommittedCapitalForm(initial={
            'investor': self.investor.id,  # Pass ID instead of object
            'date': timezone.now().date()
        })
        return context
    
    def post(self, request, *args, **kwargs):
        self.fund = get_object_or_404(Fund, pk=self.kwargs['fund_pk'])
        self.investor = get_object_or_404(Investor, pk=self.kwargs['investor_pk'])
        
        form = CommittedCapitalForm(request.POST)
        if form.is_valid():
            commitment = form.save(commit=False)
            commitment.fund = self.fund
            commitment.investor = self.investor  # Ensure investor is set
            commitment.save()
            messages.success(request, f'Additional commitment added for {self.investor.name}')
            return redirect('investor_commitments', fund_pk=self.fund.pk, investor_pk=self.investor.pk)
        else:
            # Debug form errors
            print("Form errors:", form.errors)
            messages.error(request, 'Please correct the errors below.')
            
            # Return to the same page with form errors
            context = self.get_context_data()
            context['commitment_form'] = form  # Pass the form with errors
            return render(request, self.template_name, context)

# Management Fee Calculations

class FundParameterListView(ListView):
    model = FundParameter
    template_name = "funds/fund_parameter_list.html"
    context_object_name = 'parameters'
    
    def get_queryset(self):
        return FundParameter.objects.select_related('fund').all()

class FundParameterCreateView(CreateView):
    model = FundParameter
    form_class = FundParameterForm
    template_name = "funds/fund_parameter_form.html"
    
    def get_success_url(self):
        return reverse_lazy('fund_parameter_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        return context
    
    def form_valid(self, form):
        messages.success(self.request, f'Parameters created for {form.instance.fund.name}')
        return super().form_valid(form)

class FundParameterUpdateView(UpdateView):
    model = FundParameter
    form_class = FundParameterForm
    template_name = "funds/fund_parameter_form.html"
    
    def get_success_url(self):
        return reverse_lazy('fund_parameter_list')
    
    def form_valid(self, form):
        messages.success(self.request, f'Parameters updated for {self.object.fund.name}')
        return super().form_valid(form)

class CalculateManagementFeesView(View):
    """Web-based management fee calculation"""
    
    def get(self, request, *args, **kwargs):
        """Render the fee calculation page"""
        context = {
            'today': timezone.now().date(),
            'funds': Fund.objects.all(),
            'recent_fees': ManagementFees.objects.select_related('fund')
                                  .order_by('-created_at')[:10]
        }
        return render(request, 'funds/calculate_management_fees.html', context)
    
    def post(self, request, *args, **kwargs):
        fund_id = request.POST.get('fund_id')
        calculation_date_str = request.POST.get('calculation_date')
        force_calculation = request.POST.get('force', False)
        
        try:
            if calculation_date_str:
                calculation_date = datetime.strptime(calculation_date_str, '%Y-%m-%d').date()
            else:
                calculation_date = timezone.now().date()
            
            if fund_id:
                # Calculate for specific fund
                fund = Fund.objects.get(id=fund_id)
                results = self.calculate_single_fund(fund, calculation_date, force_calculation)
            else:
                # Calculate for all funds
                results = []
                for fund in Fund.objects.all():
                    result = self.calculate_single_fund(fund, calculation_date, force_calculation)
                    results.append(result)
            
            return JsonResponse({
                'success': True,
                'results': results,
                'calculation_date': calculation_date_str or calculation_date.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def calculate_single_fund(self, fund, calculation_date, force_calculation):
        """Calculate fees for a single fund (reusing your command logic)"""
        try:
            params = FundParameter.objects.get(fund=fund)
            
            # Import your command logic
            from .management.commands.calculate_management_fees import Command
            cmd = Command()
            
            if not cmd.is_fee_calculation_day(calculation_date, params):
                return {
                    'fund': fund.name,
                    'status': 'skipped',
                    'reason': 'Not a fee calculation day',
                    'calculation_date': calculation_date.isoformat()
                }
            
            period_start, period_end = cmd.get_period_dates(calculation_date, params)
            
            # Check if period already exists
            if not force_calculation and ManagementFees.objects.filter(
                fund=fund,
                period_start_date=period_start,
                period_end_date=period_end
            ).exists():
                return {
                    'fund': fund.name,
                    'status': 'skipped',
                    'reason': 'Fee period already exists',
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat()
                }
            
            # Calculate the fee
            result = cmd.calculate_management_fee(fund, period_start, period_end, params)
            
            # Create the fee record
            fee_record = cmd.create_fee_record(fund, period_start, period_end, result, params)
            
            if fee_record:
                return {
                    'fund': fund.name,
                    'status': 'success',
                    'amount': float(result['gross_fee_amount']),
                    'basis': result['basis_type'],
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat(),
                    'fee_id': fee_record.id
                }
            else:
                return {
                    'fund': fund.name,
                    'status': 'failed',
                    'reason': 'Failed to create fee record'
                }
                
        except FundParameter.DoesNotExist:
            return {
                'fund': fund.name,
                'status': 'skipped',
                'reason': 'No fund parameters configured'
            }
        except Exception as e:
            return {
                'fund': fund.name,
                'status': 'error',
                'reason': str(e)
            }

class ManagementFeeListView(ListView):
    model = ManagementFees
    template_name = "funds/management_fee_list.html"
    context_object_name = 'fees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = ManagementFees.objects.select_related('fund', 'capital_call__notice_number').order_by('-period_end_date')
        
        # Apply filters
        fund_filter = self.request.GET.get('fund')
        status_filter = self.request.GET.get('status')
        period_filter = self.request.GET.get('period')
        
        if fund_filter:
            queryset = queryset.filter(fund_id=fund_filter)
        
        if status_filter == 'paid':
            queryset = queryset.filter(paid=True)
        elif status_filter == 'unpaid':
            queryset = queryset.filter(paid=False)
        
        if period_filter:
            # Filter by year-month of period end date
            queryset = queryset.filter(period_end_date__startswith=period_filter)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['funds'] = Fund.objects.all()
        
        # Calculate summary statistics
        queryset = self.get_queryset()
        context['total_fees'] = queryset.aggregate(total=Sum('gross_fee_amount'))['total'] or 0
        context['paid_fees'] = queryset.filter(paid=True).aggregate(total=Sum('gross_fee_amount'))['total'] or 0
        context['unpaid_fees'] = queryset.filter(paid=False).aggregate(total=Sum('gross_fee_amount'))['total'] or 0
        
        return context

def mark_fee_paid(request, fee_id):
    """Mark a management fee as paid"""
    if request.method == 'POST':
        fee = get_object_or_404(ManagementFees, id=fee_id)
        fee.paid = True
        fee.save()
        messages.success(request, f'Fee for {fee.fund.name} marked as paid.')
    return redirect('management_fee_list')

def delete_management_fee(request, fee_id):
    """Delete a management fee record"""
    if request.method == 'POST':
        fee = get_object_or_404(ManagementFees, id=fee_id)
        fund_name = fee.fund.name
        fee.delete()
        messages.success(request, f'Fee record for {fund_name} deleted successfully.')
    return redirect('management_fee_list')


# Investors Administration

class InvestorsList(LoginRequiredMixin, ListView):
    model = Investor
    template_name = 'investors/investors2.html'
    context_object_name = 'investors'

    def get_queryset(self):
        # Prefetch primary contacts
        primary_contacts = InvestorContact.objects.filter(
            primary_contact=True
        ).select_related('contact')
        
        # Annotate with commitment and capital call sums
        queryset = Investor.objects.prefetch_related(
            Prefetch('investorcontact_set', 
                    queryset=primary_contacts,
                    to_attr='primary_contacts')
        ).annotate(
            total_committed=Sum('committedcapital__amount'),
            total_called=Sum('capitalcall__amount'),
            funds_count=Count('committedcapital__fund', distinct=True)
        )
        
        # Check for a search query
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(short_name__icontains=query) |
                Q(reg_no__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        investors_data = []
        total_committed = 0
        total_called = 0
        
        for investor in context['investors']:
            # Get primary contact
            primary_contact = None
            if hasattr(investor, 'primary_contacts') and investor.primary_contacts:
                primary_contact = investor.primary_contacts[0].contact
            
            # Get annotated values
            investor_committed = investor.total_committed or 0
            investor_called = investor.total_called or 0
            funds_count = investor.funds_count or 0
            
            total_committed += investor_committed
            total_called += investor_called
            
            investors_data.append({
                'investor': investor,
                'primary_contact': primary_contact,
                'total_committed': investor_committed,
                'total_called': investor_called,
                'funds_count': funds_count
            })

        context['investors_data'] = investors_data
        context['search_query'] = self.request.GET.get('q', '')
        context['total_committed'] = total_committed
        context['total_called'] = total_called
        return context

class InvestorDetail(DetailView):
    model = Investor
    template_name = 'investors/investor_overview2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investor = self.object

        investor_contacts = InvestorContact.objects.filter(
            investor = investor
            ).select_related('contact').order_by('contact__surname', 'contact__name')
                                                 
        primary_contact = investor_contacts.filter(primary_contact = True).first()

        context.update({
            'investor_contacts': investor_contacts,
            'primary_contact': primary_contact,
        })

        return context

class AddInvestor(CreateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'investors/add_investor.html'
    context_object_name = 'investors'
    success_url = reverse_lazy('investors')

    def form_valid(self, form):
        return super().form_valid(form)

class EditInvestor(UpdateView):
    model = Investor
    form_class = InvestorForm
    template_name = 'investors/edit_investor.html'
    pk_url_kwarg = 'pk'
    success_url = reverse_lazy('investors')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get primary contact for display purposes
        primary_contact = InvestorContact.objects.filter(
            investor=self.object, 
            primary_contact=True
        ).select_related('contact').first()
        
        # Get all linked contacts
        linked_contacts = InvestorContact.objects.filter(
            investor=self.object
        ).select_related('contact')
        
        context.update({
            'primary_contact': primary_contact.contact if primary_contact else None,
            'linked_contacts': linked_contacts,
            'total_contacts': linked_contacts.count(),
        })
        return context

class DeleteInvestor(DeleteView):
    model = Investor
    pk_url_kwarg = 'pk'
    template_name = "investors/confirm_delete.html"
    success_url = reverse_lazy('investors')


# Investments Administration

class InvesmentsList(LoginRequiredMixin, ListView):
    model = Investment
    template_name = 'investments/investments2.html'
    context_object_name = 'investments'


class InvestmentDetail(DetailView):
    model = Investment
    template_name = 'investments/investment_overview2.html'
    context_object_name = 'investment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['companies'] = Company.objects.all()
        return context

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

# Companies Administration

class CompaniesList(LoginRequiredMixin, ListView):
    model = Company
    template_name = 'companies/companies.html'
    context_object_name = 'companies'

class CompanyDetail(DetailView):
    model = Investment
    template_name = 'companies/company_overview.html'
    context_object_name = 'company'

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

#Contacts Administration

class ContactsList(LoginRequiredMixin, ListView):
    model = Contact
    template_name = 'contacts/contacts2.html'
    context_object_name = 'contacts'

    def get_queryset(self):
        qs = super().get_queryset().order_by('surname', 'name')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                models.Q(name__icontains=q) |
                models.Q(surname__icontains=q) |
                models.Q(email_address__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['search_query'] = self.request.GET.get('q', '')
        return ctx

class ContactDetail(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = 'contacts/contact_overview.html'
    context_object_name = 'contact'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = self.get_object()
        
        # Get all investor links with related investor data
        investor_links = InvestorContact.objects.select_related(
            'investor', 'investor__country', 'investor__category'
        ).filter(contact=contact).order_by('investor__name')
        
        # Count statistics
        primary_count = investor_links.filter(primary_contact=True).count()
        board_rep_count = investor_links.filter(adv_board_rep=True).count()
        invest_comm_count = investor_links.filter(invest_comm_rep=True).count()
        
        context.update({
            'investor_links': investor_links,
            'primary_count': primary_count,
            'board_rep_count': board_rep_count,
            'invest_comm_count': invest_comm_count,
            'total_links': investor_links.count(),
        })
        
        return context

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

class InvestorContactCreateView(LoginRequiredMixin, CreateView):
    model = InvestorContact
    form_class = InvestorContactForm
    template_name = 'contacts/investorcontact_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['contact'] = get_object_or_404(Contact, pk=self.kwargs['pk'])
        return kwargs
    
    def form_valid(self, form):
        form.instance.contact = get_object_or_404(Contact, pk=self.kwargs['pk'])
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('contact_detail', kwargs={'pk': self.kwargs['pk']})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = get_object_or_404(Contact, pk=self.kwargs['pk'])
        return context

class InvestorContactUpdateView(LoginRequiredMixin, UpdateView):
    model = InvestorContact
    form_class = InvestorContactUpdateForm
    template_name = 'contacts/investorcontact_form.html'
    pk_url_kwarg = 'link_pk'
    
    def get_success_url(self):
        return reverse('contact_detail', kwargs={'pk': self.object.contact.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the contact to the context for the template
        context['contact'] = self.object.contact
        return context

class InvestorContactDeleteView(LoginRequiredMixin, DeleteView):
    model = InvestorContact
    template_name = 'contacts/investorcontact_confirm_delete.html'
    pk_url_kwarg = 'link_pk'
    
    def get_success_url(self):
        return reverse('contact_detail', kwargs={'pk': self.object.contact.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact'] = self.object.contact
        return context

