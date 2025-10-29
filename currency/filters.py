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

    def get_ordering(self, request, queryset, view):
        params = request.query_params.get(self.ordering_param, None)
        if params is None:
            return super().get_ordering(request, queryset, view)  # Fallback to default ordering if no param

        ordering = []
        for param in params.split(','):
            param = param.strip()
            if not param:
                continue

            if hasattr(view, 'ordering_fields') and param in view.ordering_fields:
                ordering.append(view.ordering_fields[param])
            else:
                ordering.append(param)

        # Remove empty and return
        return [o for o in ordering if o]