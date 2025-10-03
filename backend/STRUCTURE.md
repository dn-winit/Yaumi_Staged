# Backend Directory Structure - Clean & Optimized

## 📁 Directory Layout
```
backend/
│
├── config/                 # Configuration Management
│   ├── settings.py        # Application settings
│   └── __init__.py        # Config exports
│
├── core/                   # Core Business Logic
│   ├── data_manager.py    # Centralized data management
│   └── __init__.py        # Core exports
│
├── routes/                 # API Endpoints (4 main features)
│   ├── dashboard.py       # Demand analytics
│   ├── forecast.py        # Predictive analytics
│   ├── recommended_order.py # Recommendation engine
│   ├── sales_supervision.py # Supervision tracking
│   └── __init__.py        # Route exports
│
├── models/                 # Data Models
│   └── data_models.py     # Pydantic models for validation
│
├── utils/                  # Utility Functions
│   └── data_processor.py  # Data processing helpers
│
├── sql/                    # SQL Query Templates
│   ├── demand_data.sql    # Demand data queries
│   ├── recent_demand.sql  # Recent demand queries
│   ├── customer_data.sql  # Customer data queries
│   ├── journey_plan.sql   # Journey plan queries
│   └── README.md          # SQL documentation
│
├── data/                   # Data Storage
│   ├── cache/             # Cached processed data
│   │   ├── customer_data.csv
│   │   ├── demand_data.csv
│   │   ├── journey_plan.csv
│   │   ├── merged_demand.csv
│   │   └── recent_demand.csv
│   └── *.csv              # Source data files
│       ├── customer_sales_data.csv
│       ├── demand_data.csv
│       ├── journey_plan_data.csv
│       ├── merged_demand_data.csv
│       └── recent_demand_data.csv
│
├── output/                 # Generated Files
│   ├── recommendations/   # Generated recommendation CSVs
│   └── supervision/       # Supervision reports
│
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── STRUCTURE.md          # This file
└── .gitignore            # Git ignore rules
```

## 🎯 API Endpoints

### Base URL: `/api/v1`

1. **Dashboard** (`/dashboard`)
   - Filter options
   - Dashboard data
   - Historical averages

2. **Forecast** (`/forecast`)
   - Forecast filter options
   - Forecast data generation

3. **Recommended Order** (`/recommended-order`)
   - Filter options
   - Generate recommendations
   - Get recommendation data

4. **Sales Supervision** (`/sales-supervision`)
   - Filter options
   - Get sales data
   - Generate recommendations for date

## 📦 Dependencies (requirements.txt)
- fastapi
- uvicorn
- pandas
- numpy
- python-multipart

## 🚀 Clean Architecture Benefits

1. **Modular Structure**: Each route handles one business domain
2. **Centralized Data**: Single data manager for all data operations
3. **Clean Imports**: No circular dependencies
4. **Cached Data**: Efficient data loading with cache
5. **Type Safety**: Pydantic models for validation
6. **No Hardcoded Paths**: Dynamic path resolution
7. **No Test Files**: Production-ready code only

## 🧹 What Was Cleaned
- Removed dynamic_supervision.py and all redistribution logic
- Removed test files and temporary scripts
- Removed __pycache__ directories
- Removed nested backend/backend folder
- Cleaned up unused imports
- Simplified to core functionality only