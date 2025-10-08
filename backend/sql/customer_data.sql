-- Optimized customer purchase history query with date filter
-- Loads ALL routes for comprehensive recommendation generation
-- Filters to last 365 days (matches MAX_DAYS_SINCE_PURCHASE in settings.py)
-- Performance: Date filter significantly reduces load time
SELECT
    s.RouteCode,
    s.CustomerCode,
    s.ItemCode,
    s.TrxDate,
    SUM(CASE WHEN s.QuantityInPCs > 0 THEN s.QuantityInPCs ELSE 0 END) AS TotalQuantity
FROM [YaumiLive].[dbo].[VW_GET_SALES_DETAILS] s
WHERE s.ItemType = 'OrderItem'
  AND s.TrxType = 'SalesInvoice'
  AND s.TrxDate >= DATEADD(day, -365, GETDATE())  -- Last 365 days only (aligns with MAX_DAYS_SINCE_PURCHASE)
GROUP BY
    s.RouteCode,
    s.CustomerCode,
    s.ItemCode,
    s.TrxDate
ORDER BY
    s.RouteCode,
    s.CustomerCode,
    s.TrxDate DESC;