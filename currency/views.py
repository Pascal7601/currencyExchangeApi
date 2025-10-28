from rest_framework.decorators import api_view
from .services import refresh_country_data
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Country
from .filters import CountryFilter, CustomOrdering
from .serializers import CountrySerializer
from django_filters.rest_framework import DjangoFilterBackend

@api_view(["POST"])
def refresh_countries(request):
    """
    fetch all countries and exhange rates from API and stores them in db
    """
    try:
        result = refresh_country_data()
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"message": f"error fetching countries: {e}"})
    
class AllCountries(generics.ListAPIView):
    """"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilter
    filter_backends = [DjangoFilterBackend, CustomOrdering]

    ordering_fields = {
        "gdp_desc": "-estimated_gdp"
    }

class CountryDetail(generics.RetrieveDestroyAPIView):
    """"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = "name"

@api_view(["GET"])
def status(request):
    """show total countries and last refresh timestamp"""
    total_countries = Country.objects.count()
    last_refresh_obj = Country.objects.order_by("-last_refreshed_at").first()

    return Response({"total_countries": total_countries, "last_refreshed_at": last_refresh_obj.last_refreshed_at})

