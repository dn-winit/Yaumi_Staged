# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and ODBC driver
RUN apt-get update && \
    apt-get install -y curl gnupg2 apt-transport-https ca-certificates && \
    # Add Microsoft GPG key (modern method without apt-key)
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
    # Add Microsoft repository with signed-by
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list && \
    # Install ODBC driver
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev && \
    # Clean up
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy application files
COPY backend/requirements.txt /app/backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the rest of the backend code
COPY backend /app/backend

# Expose port (Render will set PORT env var)
EXPOSE 10000

# Run the application from backend directory
WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1
