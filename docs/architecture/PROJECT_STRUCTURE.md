# Yaumi Analytics Platform - Project Structure

## Directory Organization

```
webapp/
├── backend/                    # Backend API (FastAPI)
│   ├── config/                # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py        # Centralized settings (all paths dynamic)
│   │
│   ├── core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── data_manager.py    # Centralized data management
│   │   └── dynamic_supervisor.py # Dynamic supervision session manager
│   │
│   ├── data/                  # Data storage
│   │   ├── cache/            # Cached data files
│   │   └── sql/              # SQL query files
│   │
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   └── data_models.py   # Pydantic models
│   │
│   ├── output/               # Generated output files
│   │   ├── recommendations/  # Recommendation CSV files
│   │   └── supervision/      # Supervision reports
│   │
│   ├── routes/               # API endpoints
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── forecast.py
│   │   ├── recommended_order.py
│   │   └── sales_supervision.py
│   │
│   └── main.py               # FastAPI application entry point
│
├── src/                      # Frontend (React + TypeScript)
│   ├── components/           # React components
│   │   ├── common/          # Shared components
│   │   ├── Dashboard/
│   │   ├── Forecast/
│   │   ├── RecommendedOrder/
│   │   ├── SalesSupervision/
│   │   └── Home/
│   │
│   ├── config/              # Frontend configuration
│   │   └── index.ts        # Centralized config (no hardcoded URLs)
│   │
│   ├── services/            # API services
│   │   └── api/
│   │       ├── client.ts   # Axios client
│   │       ├── index.ts    # API exports
│   │       └── salesSupervision.ts
│   │
│   ├── types/               # TypeScript type definitions
│   │   └── index.ts
│   │
│   ├── App.tsx             # Main App component
│   ├── index.css           # Global styles
│   └── main.tsx            # Application entry point
│
├── .env                    # Environment variables (not in git)
├── .env.example           # Example environment configuration
├── .gitignore             # Git ignore patterns
├── package.json           # Frontend dependencies
├── requirements.txt       # Backend dependencies
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite configuration
└── README.md              # Project documentation
```

## Key Features

### Dynamic Path Resolution
- **No hardcoded paths**: All paths are dynamically resolved relative to project structure
- **Environment-based configuration**: Uses .env files for environment-specific settings
- **Centralized path management**: backend/config/settings.py handles all path construction

### Clean Architecture
- **Separation of concerns**: Clear separation between frontend/backend
- **Modular design**: Each feature has its own module
- **Reusable components**: Common components shared across features
- **Type safety**: Full TypeScript support in frontend

### Data Flow
1. **Data Loading**: SQL Server → data_manager.py → In-memory cache
2. **API Layer**: FastAPI routes serve processed data
3. **Frontend**: React components consume API via centralized service layer
4. **Dynamic Supervision**: Real-time session management with redistribution logic

### Configuration Management
- **Backend**: All settings in `backend/config/settings.py`
- **Frontend**: All settings in `src/config/index.ts`
- **Environment**: `.env` file for environment-specific values

## Development Setup

1. Copy `.env.example` to `.env` and update values
2. Install backend dependencies: `pip install -r requirements.txt`
3. Install frontend dependencies: `npm install`
4. Run backend: `python backend/main.py`
5. Run frontend: `npm run dev`

## Production Considerations

- All paths are relative/dynamic - works across different environments
- Database credentials should be set via environment variables
- CORS origins configured via environment variables
- API base URL configurable for different deployments
- Cache and output directories created automatically

## Recent Optimizations (Latest)

### Code Structure Optimization
- ✅ **Removed redundant legacy code**: Cleaned up duplicate API functions
- ✅ **Streamlined API services**: Main api.ts now only contains clean re-exports
- ✅ **Removed test files**: Eliminated test_db_connection.py from production
- ✅ **Professional integration**: All components properly integrated with clean workflow
- ✅ **Eliminated redundancy**: No duplicate code or unnecessary files

### AI Analysis Enhancement
- ✅ **Redesigned prompts**: Sales supervisor style, concise and actionable (150-200 words max)
- ✅ **Button names optimized**: "Review" instead of "AI", "Route Summary", "End of Day Report"
- ✅ **Simplified popups**: Clean text display instead of complex interactive cards
- ✅ **Quick overview format**: Designed for 30-second scan by busy supervisors

### Professional Standards
- ✅ **Clean codebase**: No redundant files or unnecessary complexity
- ✅ **Optimal workflow**: Efficient data flow from backend to frontend
- ✅ **Well-structured folders**: Logical organization with clear separation of concerns
- ✅ **Production-ready**: All test files removed, only production code remains