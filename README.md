# Yaumi Analytics Platform

Professional analytics platform for demand forecasting, inventory optimization, and sales supervision.

## Features

- **Demand Dashboard**: Historical sales analytics and insights
- **Demand Forecast**: Advanced predictive analytics
- **Recommended Orders**: Intelligent order recommendations
- **Sales Supervision**: Real-time route monitoring and inventory management

## Architecture

```
webapp/
├── backend/               # FastAPI Backend
│   ├── main.py           # Application entry point
│   ├── config.py         # Backend configuration
│   ├── routes/           # API endpoints
│   ├── models/           # Data models
│   ├── utils/            # Utility functions
│   └── static/           # Data files (CSV)
│
└── src/                  # React Frontend
    ├── components/       # UI components
    ├── services/         # API services
    ├── types/           # TypeScript types
    ├── config/          # Frontend configuration
    └── App.tsx          # Main application
```

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Pandas** - Data processing and analysis
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Frontend
- **React** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS
- **Recharts** - Data visualization
- **Vite** - Build tool

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
# Navigate to webapp directory
cd webapp

# Install Python dependencies
pip install -r requirements.txt

# Run backend server
cd backend
python main.py
```

Backend will be available at: http://localhost:8000

### Frontend Setup

```bash
# From webapp directory
npm install

# Run development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## Data Requirements

Place the following CSV files in `backend/static/`:
- `demand_data.csv` - Historical demand data
- `customer_sales_data.csv` - Customer purchase history
- `journey_plan_data.csv` - Route planning data
- `merged_daily_forecasts.csv` - Daily forecast data
- `merged_weekly_forecasts.csv` - Weekly forecast data
- `merged_monthly_forecasts.csv` - Monthly forecast data
- `processed_historical_predictions.csv` - Historical predictions

## API Documentation

With the backend running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Running Both Servers

```bash
# Terminal 1 - Backend
cd webapp/backend
python main.py

# Terminal 2 - Frontend
cd webapp
npm run dev
```

### Building for Production

```bash
# Build frontend
npm run build

# Output will be in dist/ directory
```

## Project Structure

### Backend Routes
- `/api/dashboard/*` - Dashboard data endpoints
- `/api/forecast/*` - Forecast data endpoints
- `/api/recommended-order/*` - Order recommendation endpoints
- `/api/sales-supervision/*` - Sales supervision endpoints

### Frontend Components
- `Dashboard/` - Sales analytics dashboard
- `Forecast/` - Forecasting interface
- `RecommendedOrder/` - Order recommendations
- `SalesSupervision/` - Sales monitoring
- `Home/` - Landing page
- `common/` - Shared components

## Configuration

### Backend (`backend/config.py`)
- API prefix and version
- CORS origins
- Data file paths
- Pagination settings

### Frontend (`src/config/index.ts`)
- API base URL
- App settings
- Feature flags
- UI configurations

## Environment Variables

### Backend (.env)
```bash
# Required
GROQ_API_KEY=your_analytics_api_key_here

# Optional
LOG_LEVEL=INFO  # Logging level
```

### Frontend (.env)
```bash
# Optional - defaults to local backend
VITE_API_URL=http://localhost:8000/api
```

## Features in Detail

### Dashboard
- View historical sales trends
- Filter by route, item, and date range
- Interactive charts and tables
- Export capabilities

### Forecast
- Advanced predictive analytics
- Daily, weekly, and monthly views
- Accuracy metrics
- Trend analysis

### Recommended Order
- Customer-specific recommendations
- Item quantity suggestions
- Order optimization
- Historical performance

### Sales Supervision
- Real-time sales tracking with analytics engine
- FMCG-optimized performance scoring (75-120% optimal range)
- Dynamic inventory redistribution during route execution
- Customer visit tracking with individual performance analysis
- Route summary with comprehensive metrics dashboard
- Automated actionable insights for field supervision

## Support

For issues or questions, please check the documentation or contact the development team.