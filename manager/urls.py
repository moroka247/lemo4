import debug_toolbar
from django.conf import settings
from django.conf.urls.static import static
from pprint import pprint
from rest_framework_nested import routers
from django.urls import path, include
from . import views
from . views import *


router = routers.DefaultRouter()
router.register('funds-list', views.FundViewSet, basename='funds-list')
router.register('investors-list', views.InvestorViewSet, basename='investors-list')
router.register('fund-close', views.FundCloseViewSet, basename='fund-close')
router.register('investor-types', views.InvestorTypesViewSet, basename='investor-types')
router.register('fund-structures', views.FundStructuresViewSet, basename='fund-strtuctures')
router.register('investor-contacts', views.ContactListViewSet, basename='investor-contacts')
router.register('investor-documents', views.InvestorDocumentsViewSet, basename='investor-documents')
router.register('committed-capital', views.CommittedCapitalViewSet, basename='committed-capital')
router.register('call-type', views.CallTypeViewSet, basename='call-type')
router.register('distribution-type', views.DistributionTypeViewSet, basename='distribution-type')
router.register('capital-call', views.CapitalCallViewSet, basename='capital-call')
router.register('distribution', views.DistributionViewSet, basename='distribution')
router.register('company', views.CompanyViewSet, basename='company')
router.register('investment', views.InvestmentViewSet, basename='investment')
router.register('disbursement', views.DisbursementViewSet, basename='disbursement')
router.register('countries', views.CountryViewSet, basename='countries')
router.register('currencies', views.CurrencyViewSet, basename='currencies')
router.register('industry', views.IndustryViewSet, basename='industry')
router.register('instrument', views.InstrumentViewSet, basename='instrument')


#investors_router = routers.NestedDefaultRouter(router, 'investors', lookup='investors_pk')
#investors_router.register('contacts',views.ContactViewSet, basename='investor-contacts')

urlpatterns = [
    path('api/',include(router.urls)),
    path('', HomePageView.as_view(), name='home'),
    path('__debug__/', include(debug_toolbar.urls)),
    # Funds
    path('funds/', FundsList.as_view(), name='funds'),
    path('funds/<int:pk>', FundDetail.as_view(), name='fund_detail'),
    path('add_fund/', AddFund.as_view(), name='add_fund'),
    path('edit_fund/<int:pk>/', EditFund.as_view(), name='edit_fund'),
    path('delete_fund/<int:pk>/', DeleteFund.as_view(), name='delete_fund'),
    #path('fund/<int:pk>/commit/', CommittedCapitalSubmitView.as_view(), name='fund_close'),
    path('fund/<int:pk>/commit/', CommittedCapitalCreateView.as_view(), name='fund_close'),
    path('fund/<int:pk>/capital_call/', CapitalCallView.as_view(), name='capital_call'),
    # Investors
    path('investors/', InvestorsList.as_view(), name='investors'),
    path('investors/<int:pk>', InvestorDetail.as_view(), name='investor_detail'),
    path('add_investor/', AddInvestor.as_view(), name='add_investor'),
    path('edit_investor/<int:pk>/', EditInvestor.as_view(), name='edit_investor'),
    path('delete_investor/<int:pk>/', DeleteInvestor.as_view(), name='delete_investor'),
    # Investments
    path('investments/', InvesmentsList.as_view(),name='investments'),
    path('investments/<int:pk>', InvestmentDetail.as_view(),name='investment_detail'),
    path('add_investment/', AddInvestment.as_view(), name='add_investment'),
    path('edit_investment/<int:pk>/', EditInvestment.as_view(), name='edit_investment'),
    path('delete_investment/<int:pk>/', DeleteInvestment.as_view(), name='delete_investment'),
    #Companies
    path('companies/', CompaniesList.as_view(), name='companies'),
    path('companies/<int:pk>', CompanyDetail.as_view(),name='company_detail'),
    path('add_company/', AddCompany.as_view(), name='add_company'),
    path('edit_company/<int:pk>/', EditCompany.as_view(), name='edit_company'),
    path('delete_company/<int:pk>/', DeleteCompany.as_view(), name='delete_company'),
    # Contacts
    path('contacts/', ContactsList.as_view(), name='contacts'),
    path('add_contact/', AddContact.as_view(), name='add_contact'),
    path('edit_contact/<int:pk>/', EditContact.as_view(), name='edit_contact'),
    path('delete_contact/<int:pk>/', DeleteContact.as_view(), name='delete_contact'),
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

#pprint(urlpatterns)