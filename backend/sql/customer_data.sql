-- Optimized customer purchase history query with date filter
-- Filters to route 1004 and last 365 days (matches MAX_DAYS_SINCE_PURCHASE in settings.py)
-- Performance: Route + date filter reduces load time from ~43s to ~2-3s
-- Note: Backend generates for ALL routes when needed, but loads route 1004 data for fast startup
SELECT
    s.RouteCode,
    s.CustomerCode,
    s.ItemCode,
    s.TrxDate,
    SUM(CASE WHEN s.QuantityInPCs > 0 THEN s.QuantityInPCs ELSE 0 END) AS TotalQuantity
FROM [YaumiLive].[dbo].[VW_GET_SALES_DETAILS] s
WHERE s.RouteCode = '1004'
  AND s.ItemType = 'OrderItem'
  AND s.TrxType = 'SalesInvoice'
  AND s.TrxDate >= DATEADD(day, -365, GETDATE())  -- Last 365 days only (aligns with MAX_DAYS_SINCE_PURCHASE)
GROUP BY
    s.RouteCode,
    s.CustomerCode,
    s.ItemCode,
    s.TrxDate
ORDER BY
    s.CustomerCode,
    s.TrxDate DESC;