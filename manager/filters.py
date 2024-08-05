from .models import Fund, Investor
from django_filters.rest_framework import FilterSet

class FundFilter(FilterSet):
    class Meta:
        model = Fund
        fields = {
            'structure': ['exact'],
        }

