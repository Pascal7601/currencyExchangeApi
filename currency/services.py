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


@transaction.atomic
def refresh_country_data():
    """
    Main service function to fetch, process, and cache data in the DB.
    This version is optimized for bulk operations to prevent timeouts.
    """
    print("Starting data sync (FAST, BULK mode)...")
    last_refresh_time = timezone.now()

    # 1. Fetch data from external APIs
    rates_data = _fetch_api_data(RATES_API, "ExchangeRates API")['rates']
    country_data = _fetch_api_data(COUNTRY_API, "RestCountries API")

    if not rates_data or not country_data:
        raise ExternalApiException(source_name="APIs returned empty data.")

    # 2. Process data in memory
    
    # Get all existing countries from DB in ONE query
    existing_countries = {c.name.lower(): c for c in Country.objects.all()}
    
    countries_to_create = []
    countries_to_update = []
    
    # Fields that we will update in bulk
    update_fields = [
        'capital', 'region', 'population', 'flag_url',
        'currency_code', 'exchange_rate', 'estimated_gdp'
    ]

    for country in country_data:
        name = country.get('name')
        if not name:
            continue
        
        population = country.get('population')
        currency_list = country.get('currencies')

        # --- Initialize defaults ---
        currency_code = None
        exchange_rate = None
        estimated_gdp = None

        # --- Apply Currency Logic ---
        if currency_list and isinstance(currency_list, list) and len(currency_list) > 0:
            code = currency_list[0].get('code')
            if code and code != '(none)':
                currency_code = code
                if currency_code in rates_data:
                    exchange_rate = Decimal(rates_data[currency_code])
                    if population and exchange_rate > 0:
                        multiplier = Decimal(random.uniform(1000, 2000))
                        estimated_gdp = (Decimal(population) * multiplier) / exchange_rate
                else:
                    estimated_gdp = None # Code not found, set GDP to null
        else:
            estimated_gdp = 0 # Empty currency array, set GDP to 0

        # --- Check if country exists and sort into lists ---
        if name.lower() in existing_countries:
            # Country exists, add to UPDATE list
            obj = existing_countries[name.lower()]
            obj.capital = country.get('capital')
            obj.region = country.get('region')
            obj.population = population
            obj.flag_url = country.get('flag')
            obj.currency_code = currency_code
            obj.exchange_rate = exchange_rate
            obj.estimated_gdp = estimated_gdp
            countries_to_update.append(obj)
        else:
            # Country is new, add to CREATE list
            countries_to_create.append(
                Country(
                    name=name,
                    capital=country.get('capital'),
                    region=country.get('region'),
                    population=population,
                    flag_url=country.get('flag'),
                    currency_code=currency_code,
                    exchange_rate=exchange_rate,
                    estimated_gdp=estimated_gdp
                )
            )

    # 3. Perform bulk database operations (2 queries total)
    if countries_to_create:
        Country.objects.bulk_create(countries_to_create)
        print(f"Created {len(countries_to_create)} new countries.")
        
    if countries_to_update:
        Country.objects.bulk_update(countries_to_update, update_fields)
        print(f"Updated {len(countries_to_update)} existing countries.")

    # 4. Generate Summary Image
    total_countries = len(existing_countries) + len(countries_to_create)
    top_5 = Country.objects.order_by('-estimated_gdp').values('name', 'estimated_gdp')[:5]
    _generate_summary_image(total_countries, top_5, last_refresh_time)

    return {
        "status": "success",
        "created": len(countries_to_create),
        "updated": len(countries_to_update),
        "timestamp": last_refresh_time
    }

