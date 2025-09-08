# In your signals.py file (create if it doesn't exist)
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Fund, FundParameter, Month, FeeFrequency, FeeBasis
from datetime import date, timedelta

@receiver(post_save, sender=Fund)
def create_default_fund_parameters(sender, instance, created, **kwargs):
    if created:
        # Create default fund parameters
        FundParameter.objects.create(
            fund=instance,
            fee_frequency=FeeFrequency.QUARTERLY,
            investment_period_fee_basis=FeeBasis.COMMITTED_CAPITAL,
            divest_period_fee_basis=FeeBasis.INVESTED_CAPITAL,
            fiscal_year_end_month=Month.DECEMBER,
            investment_period_end_date=date.today() + timedelta(days=365*5)  # 5 years from now
        )
