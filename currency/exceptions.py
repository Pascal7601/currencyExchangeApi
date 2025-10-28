from rest_framework.exceptions import APIException

class ExternalApiException(APIException):
    status_code = 503
    default_detail = 'External data source unavailable.'
    
    def __init__(self, detail=None, code=None, source_name=None):
        if detail is None:
            detail = self.default_detail
        if source_name:
            # This allows to pass the specific API name
            detail = f"{detail} (Details: {source_name})"
        
        super().__init__(detail, code)