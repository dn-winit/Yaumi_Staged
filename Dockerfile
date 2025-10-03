# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and ODBC driver
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https && \
    # Add Microsoft repository
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    # Install ODBC driver
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY backend /app

# Expose port (Render will set PORT env var)
EXPOSE 10000

# Run the application
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1
