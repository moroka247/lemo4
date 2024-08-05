from rest_framework import serializers
from .models import *

class InvestorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorType
        fields = '__all__'

class InvestorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investor
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

class InvestorDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestorDocument
        fields = '__all__'

class FundStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundStructure
        fields = '__all__'

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = '__all__'

class FundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fund
        fields = '__all__'

    life = serializers.SerializerMethodField(method_name='get_fund_life')

    @staticmethod
    def get_fund_life(fund: Fund):
        return fund.investment_period + fund.divestment_period

class FundCloseSerializer(serializers.ModelSerializer):
    class Meta:
        model = FundClose
        fields = '__all__'

class AllocationRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllocationRule
        fields = '__all__'

class CallTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CallType
        fields = '__all__'

class DistributionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = DistributionType
        fields = '__all__'

class CapitalCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapitalCall
        fields = '__all__'

class DistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Distribution
        fields = '__all__'

class IndustrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Industry
        fields = '__all__'

class InstrumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Instrument
        fields = '__all__'

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'

class InvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = '__all__'

class DisbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = '__all__'

class CommittedCapitalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommittedCapital
        fields = '__all__'