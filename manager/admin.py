from django.contrib import admin
from . models import *

admin.site.register(Currency)
admin.site.register(Country)
admin.site.register(FundStructure)
admin.site.register(Fund)
admin.site.register(FundClose)
admin.site.register(InvestorType)
admin.site.register(Investor)
admin.site.register(Contact)
admin.site.register(Investment)

