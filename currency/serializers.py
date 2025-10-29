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
        errors = {}
        # Check for required fields on creation.
        # On update (PATCH), fields are optional.
        if not self.instance:
            if not data.get('name'):
                errors['name'] = 'This field is required.'
            if not data.get('population'):
                errors['population'] = 'This field is required.'
            if not data.get('currency_code'):
                errors['currency_code'] = 'This field is required.'
        
        if errors:
            raise serializers.ValidationError({
                "error": "Validation failed",
                "details": errors
            })
        return data