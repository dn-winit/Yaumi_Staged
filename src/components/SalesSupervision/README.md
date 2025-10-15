# Sales Supervision Module

Production-level modular architecture for the Sales Supervision feature.

## 📁 Folder Structure

```
SalesSupervision/
├── README.md                           # This file
├── index.ts                            # Module exports
├── SalesSupervision.tsx                # Main component (orchestrator)
├── types.ts                            # TypeScript interfaces and types
│
├── hooks/                              # Custom React hooks
│   └── useSalesSupervisionState.ts    # State management hook
│
├── utils/                              # Utility functions
│   └── helpers.ts                      # Helper functions (formatting, calculations, etc.)
│
└── components/                         # Sub-components
    └── DemandSection.tsx               # Demand data display component
```

## 🎯 Architecture Overview

### Main Component (`SalesSupervision.tsx`)
- **Role**: Orchestrator component
- **Responsibilities**:
  - Coordinates business logic
  - Handles API calls
  - Manages event handlers
  - Renders UI structure

### Types (`types.ts`)
- All TypeScript interfaces and type definitions
- Centralized type management
- Ensures type safety across the module

### State Hook (`hooks/useSalesSupervisionState.ts`)
- Consolidates all useState declarations
- Provides clean state management API
- Includes resetState utility for filter changes

### Utilities (`utils/helpers.ts`)
- Pure functions for calculations
- Formatting helpers
- Color/styling helpers
- Business logic helpers (accuracy calculations, throttling, etc.)

### Components (`components/`)
- Reusable UI components
- Isolated, testable components
- Clear props interfaces

## 🔧 Usage

### Importing the Main Component
```typescript
import SalesSupervision from '@/components/SalesSupervision';
```

### Importing Types
```typescript
import type { Customer, SalesData, CustomerAnalysisResult } from '@/components/SalesSupervision/types';
```

### Using Utilities
```typescript
import { formatNumber, getTierColor, calculateAccuracy } from '@/components/SalesSupervision/utils/helpers';
```

### Using State Hook
```typescript
import { useSalesSupervisionState } from '@/components/SalesSupervision/hooks/useSalesSupervisionState';

const MyComponent = () => {
  const state = useSalesSupervisionState();
  // Access: state.salesData, state.setSalesData, etc.
};
```

## 📊 State Management

The state hook manages:
- **Filter State**: routes, dates, selections
- **Data State**: sales data, recommendations
- **Loading States**: loading, refreshing, processing
- **UI State**: modals, expanded sections, editing
- **Visit Tracking**: visited customers, sequences
- **Session State**: historical/live mode, session data
- **Analysis State**: customer/route analyses, LLM caching

## 🚀 Benefits

1. **Maintainability**: Clear separation of concerns
2. **Testability**: Isolated functions and components
3. **Reusability**: Extracted components can be reused
4. **Type Safety**: Centralized type definitions
5. **Performance**: Optimized state management
6. **Scalability**: Easy to extend with new features
7. **Developer Experience**: Clean imports, clear structure

## 📝 Best Practices

1. **Always use types** from `types.ts` - never duplicate interfaces
2. **Use helper functions** from `utils/helpers.ts` - keep components clean
3. **Extract new components** when a section exceeds 100 lines
4. **Update this README** when adding new modules
5. **Keep handlers in main component** - they coordinate business logic
6. **Use the state hook** - never useState directly in main component for shared state

## 🔐 Production Standards

✅ **Type Safety**: Full TypeScript coverage
✅ **No Breaking Changes**: All existing functionality preserved
✅ **Clean Architecture**: SOLID principles applied
✅ **Documented**: Clear comments and documentation
✅ **Tested**: Build passes without errors
✅ **Consistent**: Follows project conventions
