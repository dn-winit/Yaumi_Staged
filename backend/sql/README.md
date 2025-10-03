# SQL Queries Directory

Place your SQL query files here:

- `demand_data.sql` - Historical demand data query
- `recent_demand.sql` - Recent demand data query  
- `customer_data.sql` - Customer sales data query
- `journey_plan.sql` - Journey plan data query

The system will automatically look for these files in:
1. This directory (`backend/sql/`)
2. Project root `sql/` directory
3. External data path if configured in environment

Files are dynamically located - no hardcoded paths!