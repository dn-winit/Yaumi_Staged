#!/bin/bash
# Build script for Render - Installs SQL Server ODBC Driver

set -e  # Exit on error

echo "Installing Microsoft ODBC Driver for SQL Server..."

# Install dependencies
apt-get update
apt-get install -y curl gnupg2

# Add Microsoft repository
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update and install ODBC driver
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Install unixODBC
apt-get install -y unixodbc-dev

echo "ODBC Driver installed successfully!"

# Install Python dependencies
cd backend
pip install -r requirements.txt

echo "Build complete!"
