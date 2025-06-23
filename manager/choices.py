from django.db import models

class FeeFrequency(models.TextChoices):
    MONTHLY = "M", "Monthly"
    QUARTERLY = "Q", "Quarterly"
    SEMI_ANNUALLY = "S", "Semi-Annually"
    ANNUALLY = "A", "Annually"

class FeeBasis(models.TextChoices):
    COMMITTED_CAPITAL = "C", "Committed-Capital"
    INVESTED_CAPITAL = "I", "Invested-Capital"
    NET_ASSET_VALUE = "A", "Net-Asset-Value"

