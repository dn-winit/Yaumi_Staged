-- Optimized journey plan query with date filter
-- Loads last 30 days + next 30 days (covers historical analysis + upcoming plans)
-- Performance: Reduces dataset from ~34k to ~2k rows
Select *
from [YaumiLive].[dbo].[VW_GET_JOURNEYPLAN_DETAILS]
where RouteCode = 1004
  AND JourneyDate >= DATEADD(day, -30, GETDATE())  -- Last 30 days
  AND JourneyDate <= DATEADD(day, 30, GETDATE())   -- Next 30 days