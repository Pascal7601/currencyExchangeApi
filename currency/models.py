from django.db import models
import random
import uuid
from decimal import Decimal
from django.core.validators import MinValueValidator
# Create your models here.
class Country(models.Model):
   """
    id — auto-generated
   name — required
   capital — optional
   region — optional
   population — required
   currency_code — required
   exchange_rate — required
   estimated_gdp — computed from population × random(1000–2000) ÷ exchange_rate
   flag_url — optional
   last_refreshed_at — auto timestamp
   """
   id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
   name = models.CharField(max_length=100, null=False, blank=False, unique=True)
   capital = models.CharField(max_length=100, blank=True, null=True)
   region = models.CharField(max_length=100, blank=True, null=True)
   population = models.BigIntegerField(blank=True, null=True)
   currency_code = models.CharField(max_length=5, blank=False, null=True)
   estimated_gdp = models.DecimalField(max_digits=20, decimal_places=2, blank=True, editable=False, null=True)
   exchange_rate = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
   flag_url = models.URLField(max_length=255, blank=True, null=True)
   last_refreshed_at = models.DateTimeField(auto_now=True)

   def __str__(self):
      return f"{self.name}"