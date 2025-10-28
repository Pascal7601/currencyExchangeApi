import requests
from typing import List
from .models import Country
from django.db import transaction
from decimal import Decimal

COUNTRY_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
RATES_API = "https://open.er-api.com/v6/latest/USD"

def get_country_data():
    """Fetch country data from api"""
    response = requests.get(COUNTRY_API)

    country_data = response.json()
    return country_data

def get_exchange_rate():
    """fetch diff rates per country from api"""
    response = requests.get(RATES_API)
    data = response.json()
    return data.get("rates", {})


def refresh_country_data():
    """fills the db with data from country api"""
    country_data = get_country_data()
    rates_data = get_exchange_rate()

    Country.objects.all().delete()
    skipped = 0
    saved = 0
    try:
        with transaction.atomic():
            for country in country_data:

                name = country.get("name")
                population = country.get("population")
                currency_list = country.get("currencies")
                code = None

                if currency_list:
                    first_curr = currency_list[0]
                    code = first_curr.get("code")

                if not all([name, population, code]):
                    skipped += 1
                    continue
                exchange_rate = rates_data.get(code)
                if not exchange_rate:
                    skipped += 1
                    continue
                
                c = Country()
                c.name = name
                c.population = population
                c.currency_code = code
                c.capital = country.get("capital")
                c.region = country.get("region")
                c.flag_url = country.get("flag")
                c.exchange_rate = Decimal(exchange_rate)
                c.save()
                saved += 1
    except Exception as e:
        raise Exception("failed to populate db", e)
    return {"status": "success", "saved": saved, "skipped": skipped}

def get_country_codes(country_data) -> List:
    """
    return the country codes as a list
    """
    country_codes = []
    for country in country_data:

        currency_list = country.get("currencies")

        if currency_list:
            for curr in currency_list:
                code = curr.get("code")
                if code:
                    country_codes.append(code)
    return list(set(country_codes))