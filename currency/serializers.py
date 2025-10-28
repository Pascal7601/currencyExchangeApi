from rest_framework import serializers
from .models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            'id',
            'name',
            'capital',
            'region',
            'population',
            'currency_code',
            'exchange_rate',
            'estimated_gdp',
            'flag_url',
            'last_refreshed_at'
        ]
        read_only_fields = [
            'id', 
            'estimated_gdp', 
            'last_refreshed_at'
        ]

    def validate(self, data):
        """handles the 400 Bad Request for POST/PUT"""
        if 'population' in data and data['population'] < 0:
            raise serializers.ValidationError({"population": "Population cannot be negative."})
            
        if 'exchange_rate' in data and data['exchange_rate'] <= 0:
            raise serializers.ValidationError({"exchange_rate": "Exchange rate must be positive."})

        return data