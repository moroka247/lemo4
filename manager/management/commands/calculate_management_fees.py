# manager/management/commands/calculate_management_fees.py
from datetime import datetime, timedelta
import calendar
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum, Q
from manager.models import Fund, FundParameter, ManagementFees, CommittedCapital
from manager.choices import FeeFrequency, FeeBasis, Month

class Command(BaseCommand):
    help = 'Calculates management fees for all funds based on their schedule'

    MONTH_NUMBERS = {month.value: idx + 1 for idx, month in enumerate(Month)}

    def add_arguments(self, parser):
        parser.add_argument('--date', type=str, help='Specific date for calculation (YYYY-MM-DD)')
        parser.add_argument('--force', action='store_true', help='Force calculation')
        parser.add_argument('--fund', type=int, help='Calculate for specific fund ID only')
        parser.add_argument('--debug', action='store_true', help='Enable debug output')

    def handle(self, *args, **options):
        calculation_date = self.get_calculation_date(options)
        fund_filter = {'id': options['fund']} if options['fund'] else {}
        
        self.stdout.write(f"Calculating management fees for date: {calculation_date}")
        
        for fund in Fund.objects.filter(**fund_filter):
            self.process_fund(fund, calculation_date, options)

    def get_calculation_date(self, options):
        """Get the calculation date from options or use today"""
        if options['date']:
            return datetime.strptime(options['date'], '%Y-%m-%d').date()
        else:
            return timezone.now().date()

    def process_fund(self, fund, calculation_date, options):
        try:
            params = FundParameter.objects.get(fund=fund)
                
            if options.get('debug'):
                self.stdout.write(
                    f"DEBUG: {fund.name} - Frequency: {params.fee_frequency}, "
                    f"End Months: {params.get_period_end_months()}"
                )

            if not self.is_fee_calculation_day(calculation_date, params):
                if options.get('debug'):
                    self.stdout.write(f"DEBUG: {fund.name} - Not a fee calculation day")
                return
                
            period_start, period_end = self.get_period_dates(calculation_date, params)
            
            if options.get('debug'):
                self.stdout.write(
                    f"DEBUG: {fund.name} - Period: {period_start} to {period_end}"
                )

            if not options['force'] and self.period_exists(fund, period_start, period_end):
                self.stdout.write(self.style.WARNING(
                    f"Skipping {fund.name}: Fee already calculated for period {period_start} to {period_end}"
                ))
                return
                
            result = self.calculate_management_fee(fund, period_start, period_end, params)
            self.create_fee_record(fund, period_start, period_end, result, params)
            
        except FundParameter.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Skipping {fund.name}: No parameters"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error with {fund.name}: {str(e)}"))
            if options.get('debug'):
                import traceback
                traceback.print_exc()

    def period_exists(self, fund, period_start, period_end):
        """Check if a fee period already exists"""
        return ManagementFees.objects.filter(
            fund=fund,
            period_start_date=period_start,
            period_end_date=period_end
        ).exists()

    def create_fee_record(self, fund, period_start, period_end, result, params):
        """Safe fee record creation with validation"""
        # VALIDATION: Ensure start date is before end date
        if period_start > period_end:
            self.stdout.write(self.style.ERROR(
                f"INVALID DATE RANGE for {fund.name}: {period_start} to {period_end} - Skipping"
            ))
            return None
        
        try:
            if ManagementFees.objects.filter(
                fund=fund,
                period_start_date=period_start,
                period_end_date=period_end
            ).exists():
                self.stdout.write(self.style.WARNING(
                    f"Skipping {fund.name}: Fee already exists for period {period_start} to {period_end}"
                ))
                return None
            
            fee_record = ManagementFees.objects.create(
                fund=fund,
                period_start_date=period_start,
                period_end_date=period_end,
                calculated_basis=result['calculated_basis'],
                basis_type=result['basis_type'],
                gross_fee_amount=result['gross_fee_amount'],
                applicable_fee_rate=result['applicable_fee_rate'],
                paid=False,
                capital_call=None
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully calculated fee for {fund.name}: "
                    f"${result['gross_fee_amount']:,.2f} based on {result['basis_type']} "
                    f"for period {period_start} to {period_end}"
                )
            )
            
            return fee_record
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to create fee record for {fund.name}: {str(e)}"
            ))
            return None

    def is_fee_calculation_day(self, date, params):
        """More reliable fee calculation day check"""
        period_end_months = params.get_period_end_months()
        
        if not period_end_months:
            self.stdout.write(self.style.WARNING(
                f"No period end months defined for {params.fund.name}"
            ))
            return False

        # Get last day of current month
        last_day = self.get_last_day_of_month(date)
        
        # Check if today is the last day of any period end month
        for month_name in period_end_months:
            month_num = self.MONTH_NUMBERS[month_name]
            if date.month == month_num and date.day == last_day:
                return True
        
        return False

    def get_last_day_of_month(self, date):
        """Reliable last day of month calculation"""
        if hasattr(date, 'month') and hasattr(date, 'year'):
            year, month = date.year, date.month
            if month == 12:
                return 31
            next_month = datetime(year, month + 1, 1)
            last_day = next_month - timedelta(days=1)
            return last_day.day
        return 31  # Fallback

    def get_period_dates(self, calculation_date, params):
        """Handle all fee frequencies including non-standard quarters"""
        if params.fee_frequency == FeeFrequency.QUARTERLY:
            return self.get_quarterly_dates(calculation_date, params)
        
        elif params.fee_frequency == FeeFrequency.SEMI_ANNUALLY:
            return self.get_semi_annual_dates(calculation_date, params)
        
        elif params.fee_frequency == FeeFrequency.ANNUALLY:
            return self.get_annual_dates(calculation_date, params)
        
        elif params.fee_frequency == FeeFrequency.MONTHLY:
            return self.get_monthly_dates(calculation_date)
        
        # Default to calendar quarters
        return self.get_calendar_quarter_dates(calculation_date)

    def get_quarterly_dates(self, calculation_date, params):
        """Handle quarterly periods with custom end months, including non-standard ordering"""
        period_end_months = params.get_period_end_months()
        current_month = calculation_date.month
        year = calculation_date.year
        
        # If no custom periods, use calendar quarters
        if not period_end_months:
            return self.get_calendar_quarter_dates(calculation_date)
        
        # Sort period end months in calendar order
        sorted_month_names = self.get_sorted_period_months(period_end_months)
        sorted_month_numbers = [self.MONTH_NUMBERS[month] for month in sorted_month_names]
        
        # Find which quarter we're in based on current month
        quarter_index = None
        for i, month_num in enumerate(sorted_month_numbers):
            if current_month == month_num:
                quarter_index = i
                break
        
        # If current month is not a period end month, find the next one
        if quarter_index is None:
            for i, month_num in enumerate(sorted_month_numbers):
                if current_month <= month_num:
                    quarter_index = i
                    break
            if quarter_index is None:
                # Wrap to first quarter of next year
                quarter_index = 0
                year += 1
        
        # Get current month info
        current_month_num = sorted_month_numbers[quarter_index]
        current_month_name = sorted_month_names[quarter_index]
        
        # Calculate start date (day after previous period end)
        if quarter_index == 0:
            # First quarter - start from day after last period of previous year
            prev_month_num = sorted_month_numbers[-1]
            prev_year = year - 1
            
            prev_end_date = datetime(prev_year, prev_month_num, 1)
            prev_end_date = prev_end_date.replace(day=self.get_last_day_of_month(prev_end_date))
            start_date = prev_end_date + timedelta(days=1)
        else:
            # Start from day after previous quarter end
            prev_month_num = sorted_month_numbers[quarter_index - 1]
            prev_end_date = datetime(year, prev_month_num, 1)
            prev_end_date = prev_end_date.replace(day=self.get_last_day_of_month(prev_end_date))
            start_date = prev_end_date + timedelta(days=1)
        
        # Calculate end date (last day of current period month)
        end_date = datetime(year, current_month_num, 1)
        end_date = end_date.replace(day=self.get_last_day_of_month(end_date))
        
        # Handle year wrapping for edge cases
        if start_date > end_date:
            start_date = start_date.replace(year=year - 1)
        
        return start_date.date(), end_date.date()

    def get_sorted_period_months(self, period_end_months):
        """Return period end months sorted in calendar order with their original names"""
        if not period_end_months:
            return []
        
        # Create list of (month_number, month_name) tuples
        month_tuples = [(self.MONTH_NUMBERS[month], month) for month in period_end_months]
        # Sort by month number
        sorted_tuples = sorted(month_tuples, key=lambda x: x[0])
        # Return just the sorted month names
        return [month_name for month_num, month_name in sorted_tuples]

    def get_semi_annual_dates(self, calculation_date, params):
        """Handle semi-annual periods"""
        period_end_months = params.get_period_end_months()
        current_month = calculation_date.month
        year = calculation_date.year
        
        if not period_end_months or len(period_end_months) < 2:
            # Default semi-annual (Jun, Dec)
            if current_month <= 6:
                return datetime(year, 1, 1).date(), datetime(year, 6, 30).date()
            else:
                return datetime(year, 7, 1).date(), datetime(year, 12, 31).date()
        
        # Use custom semi-annual periods
        first_end_month = self.MONTH_NUMBERS[period_end_months[0]]
        
        if current_month <= first_end_month:
            # First half
            if first_end_month == 1:  # Special case: Jan end
                start_date = datetime(year-1, 2, 1)  # Feb 1 of previous year
                start_date = start_date.replace(day=self.get_last_day_of_month(start_date)) + timedelta(days=1)
            else:
                start_date = datetime(year, 1, 1)
            
            end_date = datetime(year, first_end_month, 1)
            end_date = end_date.replace(day=self.get_last_day_of_month(end_date))
        else:
            # Second half
            start_date = datetime(year, first_end_month, 1)
            start_date = start_date.replace(day=self.get_last_day_of_month(start_date)) + timedelta(days=1)
            
            second_end_month = self.MONTH_NUMBERS[period_end_months[1]] if len(period_end_months) > 1 else 12
            end_date = datetime(year, second_end_month, 1)
            end_date = end_date.replace(day=self.get_last_day_of_month(end_date))
        
        return start_date.date(), end_date.date()

    def get_annual_dates(self, calculation_date, params):
        """Handle annual periods"""
        period_end_months = params.get_period_end_months()
        year = calculation_date.year
        
        if not period_end_months:
            # Default annual (Dec end)
            return datetime(year, 1, 1).date(), datetime(year, 12, 31).date()
        
        # Custom annual period
        end_month_num = self.MONTH_NUMBERS[period_end_months[0]]
        end_date = datetime(year, end_month_num, 1)
        end_date = end_date.replace(day=self.get_last_day_of_month(end_date))
        
        # Start date is day after previous year's end
        prev_end_date = datetime(year-1, end_month_num, 1)
        prev_end_date = prev_end_date.replace(day=self.get_last_day_of_month(prev_end_date))
        start_date = prev_end_date + timedelta(days=1)
        
        return start_date.date(), end_date.date()

    def get_monthly_dates(self, calculation_date):
        """Handle monthly periods"""
        year = calculation_date.year
        month = calculation_date.month
        
        # Start of month
        start_date = datetime(year, month, 1)
        
        # End of month
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month+1, 1) - timedelta(days=1)
        
        return start_date.date(), end_date.date()

    def get_calendar_quarter_dates(self, calculation_date):
        """Fallback to calendar quarters"""
        year = calculation_date.year
        month = calculation_date.month
        
        if month <= 3:
            return datetime(year, 1, 1).date(), datetime(year, 3, 31).date()
        elif month <= 6:
            return datetime(year, 4, 1).date(), datetime(year, 6, 30).date()
        elif month <= 9:
            return datetime(year, 7, 1).date(), datetime(year, 9, 30).date()
        else:
            return datetime(year, 10, 1).date(), datetime(year, 12, 31).date()

    def calculate_management_fee(self, fund, period_start, period_end, params):
        """Calculate management fee for a fund on a specific date"""
        # 1. Determine the fund's phase (Investment or Divestment)
        if period_end <= params.investment_period_end_date:
            basis_type = params.investment_period_fee_basis
            fee_rate = fund.man_fee  # Full management fee during investment period
        else:
            basis_type = params.divestment_period_fee_basis
            # Reduced fee rate during divestment period (typically 50-80% of full fee)
            fee_rate = fund.man_fee * getattr(params, 'divestment_fee_percentage', 100) / 100

        # 2. Calculate the basis value based on the selected type
        if basis_type == FeeBasis.COMMITTED_CAPITAL:
            basis_value = CommittedCapital.objects.filter(
                fund=fund, 
                investor__isnull=False
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            self.stdout.write(
                self.style.NOTICE(
                    f"Found ${basis_value:,.2f} in total commitments for {fund.name}"
                )
            )
            
        elif basis_type == FeeBasis.INVESTED_CAPITAL:
            basis_value = 0
            self.stdout.write(self.style.WARNING(f"Invested Capital basis not implemented for {fund.name}"))
            
        elif basis_type == FeeBasis.NET_ASSET_VALUE:
            basis_value = 0
            self.stdout.write(self.style.WARNING(f"NAV basis not implemented for {fund.name}"))
            
        else:
            raise ValueError(f"Unknown basis type: {basis_type}")

        # 3. Calculate the gross fee amount - RESPECT ACTUAL FREQUENCY
        frequency_factors = {
            FeeFrequency.ANNUALLY: 1,
            FeeFrequency.SEMI_ANNUALLY: 2,
            FeeFrequency.QUARTERLY: 4,
            FeeFrequency.MONTHLY: 12
        }
        
        periods_per_year = frequency_factors.get(params.fee_frequency, 4)  # Default to quarterly
        
        # Calculate prorated fee if needed (using safe attribute access)
        prorate_fees = getattr(params, 'prorate_fees', False)
        if prorate_fees:
            days_in_period = (period_end - period_start).days + 1
            days_in_year = 366 if calendar.isleap(period_end.year) else 365
            gross_fee_amount = (basis_value * fee_rate * days_in_period) / days_in_year
        else:
            gross_fee_amount = (basis_value * fee_rate) / periods_per_year

        return {
            'calculated_basis': basis_value,
            'basis_type': basis_type,
            'gross_fee_amount': gross_fee_amount,
            'applicable_fee_rate': fee_rate,
            'prorated': prorate_fees
        }


    def create_fee_record(self, fund, period_start, period_end, result, params):
        """Create a DRAFT management fee record (no capital call created yet)"""
        try:
            # Check if record already exists
            if ManagementFees.objects.filter(
                fund=fund,
                period_start_date=period_start,
                period_end_date=period_end
            ).exists():
                self.stdout.write(self.style.WARNING(
                    f"Skipping {fund.name}: Fee already exists for period {period_start} to {period_end}"
                ))
                return None
            
            # Create draft fee record (paid=False, no capital_call)
            fee_record = ManagementFees.objects.create(
                fund=fund,
                period_start_date=period_start,
                period_end_date=period_end,
                calculated_basis=result['calculated_basis'],
                basis_type=result['basis_type'],
                gross_fee_amount=result['gross_fee_amount'],
                applicable_fee_rate=result['applicable_fee_rate'],
                prorated=result['prorated'],
                paid=False,
                capital_call=None  # Will be set when confirmed in the view
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Created DRAFT fee for {fund.name}: "
                    f"${result['gross_fee_amount']:,.2f} based on {result['basis_type']} "
                    f"for period {period_start} to {period_end}"
                )
            )
            
            return fee_record
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to create fee record for {fund.name}: {str(e)}"
            ))
            return None

    def calculate_prorated_fee(self, fund, period_start, period_end, params, basis_value, fee_rate):
        """Calculate prorated fee for partial periods"""
        total_days = (period_end - period_start).days + 1
        
        # Check for commitment changes during period
        commitment_changes = CommittedCapital.objects.filter(
            fund=fund,
            effective_date__gte=period_start,
            effective_date__lte=period_end
        ).order_by('effective_date')
        
        if not commitment_changes.exists():
            # No changes during period - simple calculation
            return (basis_value * fee_rate) / self.get_periods_per_year(params.fee_frequency)
        
        # Calculate weighted average basis for the period
        weighted_basis = 0
        current_start = period_start
        total_commitments = CommittedCapital.objects.filter(
            fund=fund,
            effective_date__lt=period_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        for change in commitment_changes:
            # Calculate days in current segment
            segment_days = (change.effective_date - current_start).days
            weighted_basis += total_commitments * segment_days
            
            # Update commitments
            if change.amount > 0:
                total_commitments += change.amount
            else:
                total_commitments = max(0, total_commitments + change.amount)
            
            current_start = change.effective_date
        
        # Add the final segment
        final_segment_days = (period_end - current_start).days + 1
        weighted_basis += total_commitments * final_segment_days
        
        # Calculate average daily basis
        average_daily_basis = weighted_basis / total_days
        
        # Calculate prorated annual fee
        annual_fee = average_daily_basis * fee_rate
        
        # Return prorated fee for the period
        return annual_fee * total_days / (366 if calendar.isleap(period_end.year) else 365)

    def calculate_invested_capital(self, fund, as_of_date):
        """Calculate invested capital for fee basis"""
        # Sum of all capital calls for investments (excluding management fees)
        invested_capital = CapitalCall.objects.filter(
            fund=fund,
            call_date__lte=as_of_date,
            capitalcallinvestment__isnull=False  # Only calls with investments
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Subtract any return of capital
        distributions = Distribution.objects.filter(
            fund=fund,
            distribution_date__lte=as_of_date,
            distributiontype=DistributionType.RETURN_OF_CAPITAL
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return max(0, invested_capital - distributions)

    def calculate_net_asset_value(self, fund, as_of_date):
        """Calculate Net Asset Value for fee basis"""
        # This would typically come from your accounting system
        # For now, we'll use a simplified calculation
        
        # Get latest valuation for each investment
        investments = Investment.objects.filter(fund=fund)
        nav = 0
        
        for investment in investments:
            latest_valuation = InvestmentValuation.objects.filter(
                investment=investment,
                valuation_date__lte=as_of_date
            ).order_by('-valuation_date').first()
            
            if latest_valuation:
                nav += latest_valuation.valuation_amount
        
        # Add cash and subtract liabilities
        cash_balance = CashBalance.objects.filter(
            fund=fund,
            as_of_date__lte=as_of_date
        ).order_by('-as_of_date').first()
        
        if cash_balance:
            nav += cash_balance.amount
        
        # Subtract accrued management fees
        accrued_fees = ManagementFees.objects.filter(
            fund=fund,
            period_end_date__lte=as_of_date,
            paid=False
        ).aggregate(total=Sum('gross_fee_amount'))['total'] or 0
        
        nav -= accrued_fees
        
        return max(0, nav)

