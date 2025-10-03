# Frontend (src) Directory Structure - Clean & Professional

## 📁 Directory Layout
```
src/
│
├── components/                # UI Components (Organized by Feature)
│   ├── common/               # Shared/Reusable Components
│   │   ├── CustomSelect.tsx
│   │   └── TabNavigation.tsx
│   │
│   ├── Dashboard/            # Dashboard Feature
│   │   ├── Dashboard.tsx
│   │   ├── DashboardChart.tsx
│   │   ├── DashboardFilters.tsx
│   │   ├── DashboardTable.tsx
│   │   └── HistoricalPopup.tsx
│   │
│   ├── Forecast/             # Forecast Feature
│   │   ├── Forecast.tsx
│   │   ├── ForecastChart.tsx
│   │   ├── ForecastFilters.tsx
│   │   └── ForecastTable.tsx
│   │
│   ├── RecommendedOrder/     # Recommendations Feature
│   │   ├── RecommendedOrder.tsx
│   │   ├── RecommendedOrderChart.tsx
│   │   ├── RecommendedOrderFilters.tsx
│   │   └── RecommendedOrderTable.tsx
│   │
│   ├── SalesSupervision/     # Supervision Feature
│   │   └── SalesSupervision.tsx
│   │
│   └── Home/                 # Landing Page
│       └── Home.tsx
│
├── services/                  # API Services Layer
│   ├── api/                 # Organized API Modules
│   │   ├── client.ts        # Axios configuration
│   │   ├── dashboard.ts     # Dashboard APIs
│   │   ├── forecast.ts      # Forecast APIs
│   │   ├── recommendedOrder.ts # Recommendation APIs
│   │   ├── salesSupervision.ts # Supervision APIs
│   │   └── index.ts         # Main export
│   └── api.ts               # Legacy compatibility
│
├── config/                   # Configuration
│   └── index.ts             # App configuration
│
├── types/                    # TypeScript Types
│   └── index.ts             # Type definitions
│
├── assets/                   # Static Assets
│   └── (images, fonts, etc.)
│
├── styles/                   # Global Styles
│   └── index.css            # Tailwind imports
│
├── App.tsx                   # Main App Component
├── main.tsx                  # App Entry Point
└── vite-env.d.ts            # Vite types
```

## ✅ What Makes It Professional

### 1. **Feature-Based Organization**
- Components grouped by feature (Dashboard, Forecast, etc.)
- Easy to locate and maintain
- Scalable structure

### 2. **Clean API Layer**
```
services/api/
  ├── client.ts      → Centralized axios config
  ├── dashboard.ts   → All dashboard endpoints
  ├── forecast.ts    → All forecast endpoints
  └── ...
```

### 3. **No Fake/Demo Data**
- ✅ All data from real backend
- ✅ No hardcoded mock data
- ✅ Professional API integration

### 4. **Type Safety**
- Full TypeScript coverage
- Defined interfaces for all data
- Type-safe API calls

### 5. **Configuration Management**
```typescript
config/
  └── index.ts → Single source of truth
    - API endpoints
    - App settings
    - Feature flags
```

## 🎯 Key Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **DRY (Don't Repeat Yourself)**: Shared components in `common/`
3. **Clean Imports**: Organized module structure
4. **Real Data Only**: No fake/mock data
5. **Professional Standards**: Industry best practices

## 📊 Component Structure
Each feature folder contains:
- **Main Component**: Feature entry point
- **Chart Component**: Data visualization
- **Filters Component**: User controls
- **Table Component**: Data display

## 🔌 API Integration Pattern
```typescript
// Clean API call pattern
import { dashboardAPI } from '@/services/api';

const data = await dashboardAPI.getSummary();
```

## ✨ Benefits
- **Maintainable**: Clear organization
- **Scalable**: Easy to add features
- **Professional**: Industry-standard
- **Efficient**: No redundancy
- **Real Data**: Backend integration