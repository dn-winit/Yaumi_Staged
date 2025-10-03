"""
Application messages and response templates
"""

# Error Messages
ERROR_MESSAGES = {
    'DATA_NOT_LOADED': "Data not loaded yet. Please wait for data initialization.",
    'INVALID_DATE_FORMAT': "Invalid date format. Use YYYY-MM-DD format.",
    'MISSING_PARAMETERS': "Missing required parameters: {params}",
    'NO_DATA_FOUND': "No data found for the specified filters",
    'GENERATION_FAILED': "Failed to generate recommendations: {error}",
    'DATABASE_ERROR': "Database connection error: {error}",
    'VALIDATION_ERROR': "Validation error: {error}",
    'INTERNAL_ERROR': "Internal server error occurred",
    'ROUTE_NOT_FOUND': "Route {route_code} not found",
    'CUSTOMER_NOT_FOUND': "Customer {customer_code} not found",
    'ITEM_NOT_FOUND': "Item {item_code} not found",
    'FILE_NOT_FOUND': "File not found: {filename}",
}

# Success Messages
SUCCESS_MESSAGES = {
    'DATA_LOADED': "Data loaded successfully",
    'RECOMMENDATIONS_GENERATED': "Generated {count} recommendations for {date}",
    'SESSION_INITIALIZED': "Session initialized successfully",
    'VISIT_PROCESSED': "Customer visit processed successfully",
    'ANALYSIS_COMPLETE': "Analysis completed successfully",
}

# Info Messages
INFO_MESSAGES = {
    'DATA_LOADING': "Loading data from database...",
    'CACHE_HIT': "Using cached data",
    'CACHE_MISS': "Cache miss, fetching from database",
    'GENERATING_RECOMMENDATIONS': "Generating recommendations...",
}

# HTTP Status Messages
HTTP_MESSAGES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
    503: "Service Unavailable",
}
