-- Optimized recent demand query with date-filtered JOIN
-- Only joins actual sales data for the forecast period
-- Performance: Reduces load time from ~48s to ~10-15s
SELECT
    l.TrxDate,
    l.WarehouseCode,
    l.WarehouseName,
    l.RouteCode,
    l.ItemCode,
    l.ItemName,
    l.CategoryName,
    ISNULL(CAST(r.TotalQuantity AS INT), 0) AS TotalQuantity,
	l.AvgUnitPrice,
	l.SalesValue,
    CAST(l.Predicted_Quantity AS INT) AS Predicted,
    l.Prediction_Type
FROM [YaumiAIML].[dbo].[yaumi_demand_daily_forecast_route_1004_20250901_to_20251207_run_20250912] l
LEFT JOIN (
    SELECT
        TrxDate,
        RouteCode,
        ItemCode,
        SUM(QuantityInPCs) AS TotalQuantity
    FROM [YaumiLive].[dbo].[VW_GET_SALES_DETAILS]
    WHERE RouteCode = '1004'  -- Filter to specific route (matches main query)
      AND ItemType = 'OrderItem'
      AND TrxType = 'SalesInvoice'
      AND TrxDate >= '2025-09-01'  -- Match forecast start date
      AND TrxDate <= '2025-12-07'  -- Match forecast end date
    GROUP BY TrxDate, RouteCode, ItemCode
) r
    ON l.TrxDate = r.TrxDate
    AND l.RouteCode = r.RouteCode
    AND l.ItemCode = r.ItemCode

ORDER BY TrxDate ASC;