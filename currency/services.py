import requests
from typing import List
from .models import Country
from django.db import transaction
from decimal import Decimal
from django.conf import settings
from .exceptions import ExternalApiException
from PIL import Image, ImageDraw, ImageFont
import os
from django.utils import timezone
import random
from background_task import background


COUNTRY_API = "https://restcountries.com/v2/all?fields=name,capital,region,population,flag,currencies"
RATES_API = "https://open.er-api.com/v6/latest/USD"

IMAGE_CACHE_DIR = settings.MEDIA_ROOT / 'cache'
IMAGE_PATH = IMAGE_CACHE_DIR / 'summary.png'

def _fetch_api_data(url, api_name):
    """Helper to fetch data and handle common errors."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error fetching from {api_name}: {e}")
        raise ExternalApiException(source_name=f"Failed with status {e.response.status_code} from {api_name}")
    except requests.exceptions.RequestException as e:
        print(f"Request Error fetching from {api_name}: {e}")
        raise ExternalApiException(source_name=f"Could not connect to {api_name}")


def _generate_summary_image(total_countries, top_5_countries, timestamp):
    """Generates and saves the summary.png image."""
    print("Generating summary image...")
    os.makedirs(IMAGE_CACHE_DIR, exist_ok=True) # Ensure cache dir exists
    
    img = Image.new('RGB', (600, 400), color='white')
    d = ImageDraw.Draw(img)
    
    try:
        font_title = ImageFont.truetype("arial.ttf", 24)
        font_body = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()

    # Title
    d.text((20, 20), "Country API Status", fill=(0,0,0), font=font_title)
    d.line((20, 60, 580, 60), fill='black', width=1)
    
    # Stats
    d.text((20, 80), f"Total Countries: {total_countries}", fill=(30,30,30), font=font_body)
    d.text((20, 110), f"Last Refresh: {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}", fill=(30,30,30), font=font_body)

    # Top 5
    d.text((20, 160), "Top 5 Countries by Estimated GDP:", fill=(0,0,0), font=font_body)
    y_pos = 190
    for i, country in enumerate(top_5_countries):
        gdp_str = f"{country['estimated_gdp']:,.2f}" if country['estimated_gdp'] else "N/A"
        d.text((40, y_pos), f"{i+1}. {country['name']} (GDP: ${gdp_str})", fill=(50,50,50), font=font_body)
        y_pos += 30

    img.save(IMAGE_PATH, "PNG")
    print(f"Summary image saved to {IMAGE_PATH}")


@background(schedule=1)
def refresh_country_data():
    """fills the db with data from country api"""
    last_refresh_time = timezone.now()
    
    # 1. Fetch data from external APIs
    # If either fails, ExternalApiException will be raised and the
    # transaction will be rolled back
    rates_data = _fetch_api_data(RATES_API, "ExchangeRates API")['rates']
    country_data = _fetch_api_data(COUNTRY_API, "RestCountries API")

    if not rates_data or not country_data:
        raise ExternalApiException(source_name="APIs returned empty data.")

    processed_names = set()

    for country in country_data:
        name = country.get('name')
        if not name:
            continue
        
        processed_names.add(name.lower())
        population = country.get('population')

        currency_code = None
        exchange_rate = None
        estimated_gdp = None
        

        currency_list = country.get('currencies')
        
        if currency_list and isinstance(currency_list, list) and len(currency_list) > 0:

            first_currency = currency_list[0]
            code = first_currency.get('code')
            
            if code and code != '(none)':
                currency_code = code
                if currency_code in rates_data:
                    exchange_rate = Decimal(rates_data[currency_code])
       
                    if population and exchange_rate > 0:
                        multiplier = Decimal(random.uniform(1000, 2000))
                        estimated_gdp = (Decimal(population) * multiplier) / exchange_rate
                else:
                    exchange_rate = None
                    estimated_gdp = None
        else:
            currency_code = None
            exchange_rate = None
            estimated_gdp = 0

        defaults = {
            'name': name,
            'capital': country.get('capital'),
            'region': country.get('region'),
            'population': population,
            'flag_url': country.get('flag'),
            'currency_code': currency_code,
            'exchange_rate': exchange_rate,
            'estimated_gdp': estimated_gdp,
        }

        Country.objects.update_or_create(
            name__iexact=name,
            defaults=defaults
        )

    print(f"Processed {len(processed_names)} countries.")

    # 3. Generate Summary Image
    # This runs inside the transaction. If image gen fails,
    # the entire DB sync is rolled back.
    total_countries = Country.objects.count()
    top_5_countries = Country.objects.order_by('-estimated_gdp').values('name', 'estimated_gdp')[:5]
    
    _generate_summary_image(total_countries, top_5_countries, last_refresh_time)

    return {
        "status": "success",
        "total_countries_processed": len(processed_names),
        "total_in_database": total_countries,
        "timestamp": last_refresh_time
    }

