from rest_framework.decorators import api_view
from .services import refresh_country_data
from rest_framework import generics, status
from rest_framework.response import Response
from .models import Country
from .filters import CountryFilter, CustomOrdering
from .serializers import CountrySerializer
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.http import HttpResponse, Http404
import os
from .exceptions import ExternalApiException

@api_view(["POST"])
def refresh_countries(request):
    """
    fetch all countries and exhange rates from API and stores them in db
    """
    print("refreshhh....")
    try:
        result = refresh_country_data()
        return Response(result, status=status.HTTP_200_OK)
    except ExternalApiException as e:
        return Response({"error": e.detail}, status=e.status_code)
    except Exception as e:
        return Response({"message": f"error fetching countries: {e}"})
    
class AllCountries(generics.ListAPIView):
    """"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    filterset_class = CountryFilter
    filter_backends = [DjangoFilterBackend, CustomOrdering]

    ordering_fields = {
        "gdp_desc": "-estimated_gdp",
        "gdp_asc": "estimated_gdp",
        "name": "name",
        "population": "population",
        "region": "region"
    }

class CountryDetail(generics.RetrieveDestroyAPIView):
    """"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    lookup_field = "name"

    def retrieve(self, request, *args, **kwargs):
        try:
            # Try to get the object as usual
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        except Http404:
            return Response(
                {"error": "Country not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

@api_view(["GET"])
def get_status(request):
    """show total countries and last refresh timestamp"""
    total_countries = Country.objects.count()
    last_refresh_obj = Country.objects.order_by("-last_refreshed_at").first()

    return Response({"total_countries": total_countries, "last_refreshed_at": last_refresh_obj.last_refreshed_at})

@api_view(["GET"])
def summary_image(request):
    image_path = settings.MEDIA_ROOT / 'cache' / 'summary.png'
    
    if not os.path.exists(image_path):
        return Response(
            {"error": "Summary image not found."}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    try:
        with open(image_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/png')
    except IOError as e:
        return Response(
            {"error": "Could not read image file.", "details": str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )