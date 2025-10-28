import django_filters
from .models import Country
from rest_framework import filters

class CountryFilter(django_filters.FilterSet):
    region = django_filters.CharFilter(lookup_expr="icontains")
    currency = django_filters.CharFilter(field_name="currency_code", lookup_expr="iexact")

    class Meta:
        model = Country
        fields = ["region", "currency"]

class CustomOrdering(filters.OrderingFilter):
    ordering_param = "sort"