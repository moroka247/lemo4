# manager/services.py
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import timedelta
from .models import Fund, FundParameter, ManagementFees, CommittedCapital, Investment, Valuation
from .choices import FeeBasis

def calculate_management_fee(fund, period_end_date):
    """
    Calculates the management fee for a given fund and period end date.
    Returns a dictionary with the results or raises an exception if configuration is missing.
    """
    try:
        params = FundParameter.objects.get(fund=fund)
    except FundParameter.DoesNotExist:
        raise ValueError(f"No FundParameter configuration found for fund: {fund.name}")

    # 1. Determine the fund's phase (Investment or Divestment)
    # NOTE: You'll need to add 'investment_period_end_date' to FundParameter
    if period_end_date <= params.investment_period_end_date:
        basis_type = params.investment_period_fee_basis
        phase = "Investment"
    else:
        basis_type = params.divestment_period_fee_basis
        phase = "Divestment"

    # 2. Calculate the basis value based on the selected type
    if basis_type == FeeBasis.COMMITTED_CAPITAL:
        # Sum of all commitments from finalized closes
        basis_value = CommittedCapital.objects.filter(
            fund=fund, 
            final_close=True
        ).aggregate(total=Sum('commitment_amount'))['total'] or 0
        
    elif basis_type == FeeBasis.INVESTED_CAPITAL:
        # Sum of acquisition costs for active investments (not written off)
        basis_value = Investment.objects.filter(
            fund=fund,
            is_written_off=False
        ).aggregate(total=Sum('acquisition_cost'))['total'] or 0
        
    elif basis_type == FeeBasis.NET_ASSET_VALUE:
        # Get the latest valuation for each investment as of period_end_date
        # This is a more complex query that might need optimization
        latest_valuations = Valuation.objects.filter(
            investment__fund=fund,
            valuation_date__lte=period_end_date
        ).distinct('investment').annotate(
            latest_value=Sum('value')
        )
        basis_value = sum(valuation.latest_value for valuation in latest_valuations)
        
    else:
        raise ValueError(f"Unknown basis type: {basis_type}")

    # 3. Calculate the gross fee amount
    # First, determine the period length for prorating if needed
    # This is a simplified version - actual implementation depends on fee frequency
    gross_fee_amount = basis_value * fund.management_fee_rate

    return {
        'fund': fund,
        'period_end_date': period_end_date,
        'basis_type': basis_type,
        'calculated_basis': basis_value,
        'gross_fee_amount': gross_fee_amount,
        'phase': phase,
        'applicable_fee_rate': fund.management_fee_rate
    }