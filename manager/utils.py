from decimal import Decimal, InvalidOperation
from functools import partial
from scipy.optimize import brentq

def xirr(cashflows):
    """Calculate the internal rate of return (IRR) for a series of cash flows."""
    
    if not cashflows or len(cashflows) < 2:
        return None  # IRR requires at least two cash flows

    try:
        # Extract amounts and convert to Decimal
        amounts = [Decimal(str(cf[1])) for cf in cashflows]

        # Convert dates to days from the first cashflow date
        base_date = cashflows[0][0]
        days = [(cf[0] - base_date).days for cf in cashflows]

        # Define npv function that takes rate, amounts, and days
        def npv(rate, amounts, days):
            rate = Decimal(str(rate))  # Ensure rate is Decimal
            return sum(float(amounts[i]) / ((float(Decimal(1)) + float(rate)) ** (float(days[i]) / 365)) for i in range(len(amounts)))

        # Create a partial function for npv, binding amounts and days
        npv_with_args = partial(npv, amounts=amounts, days=days)

        # Try solving IRR using Brent’s method with a wider search range
        try:
            irr = brentq(npv_with_args, -0.99, 10)  # IRR is typically between -99% and 1000%
            return float(irr)  # Convert the result to float for compatibility
        except ValueError:
            return None  # If it fails, return None

    except (InvalidOperation, ValueError, OverflowError):
        return None  # Handle any calculation failures