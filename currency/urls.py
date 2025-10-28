from django.urls import path
from . import views


urlpatterns = [
    path('countries/refresh', views.refresh_countries),
    path('countries', views.AllCountries.as_view()),
    path("countries/<str:name>", views.CountryDetail.as_view()),
    path("status", views.get_status),
    path("countries/image", views.summary_image)
]