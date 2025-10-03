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
GROUP BY 
    s.RouteCode,
    s.CustomerCode,
    s.ItemCode,
    s.TrxDate
ORDER BY 
    s.CustomerCode,
    s.TrxDate DESC;