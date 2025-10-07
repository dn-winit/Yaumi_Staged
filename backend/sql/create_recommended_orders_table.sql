-- Create table for storing daily recommended orders
-- Database: YaumiAIML
-- Run this ONCE to create the table

USE [YaumiAIML];
GO

-- SAFE CHECK: Abort if table already exists (prevents accidental data loss)
IF OBJECT_ID('[dbo].[tbl_recommended_orders]', 'U') IS NOT NULL
BEGIN
    PRINT 'WARNING: Table [tbl_recommended_orders] already exists!';
    PRINT 'Script aborted to prevent data loss.';
    PRINT 'If you want to recreate it, manually drop the table first.';
    RETURN;
END
GO

PRINT 'Creating table [tbl_recommended_orders]...';
GO

CREATE TABLE [dbo].[tbl_recommended_orders] (
    -- Primary key
    id BIGINT IDENTITY(1,1) PRIMARY KEY,

    -- Core identifiers
    trx_date DATE NOT NULL,
    route_code VARCHAR(50) NOT NULL,
    customer_code VARCHAR(50) NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_name NVARCHAR(255),

    -- Recommendation quantities
    actual_quantity INT DEFAULT 0,
    recommended_quantity INT NOT NULL,

    -- Recommendation metadata
    tier VARCHAR(50),
    van_load INT,
    priority_score DECIMAL(5,2),

    -- Performance metrics
    avg_quantity_per_visit INT,
    days_since_last_purchase INT,
    purchase_cycle_days DECIMAL(10,2),
    frequency_percent DECIMAL(5,2),

    -- System metadata
    generated_at DATETIME DEFAULT GETDATE(),
    generated_by VARCHAR(100) DEFAULT 'SYSTEM_CRON',
    is_active BIT DEFAULT 1,

    -- Ensure uniqueness per date/route/customer/item
    CONSTRAINT UQ_recommendation_daily UNIQUE (trx_date, route_code, customer_code, item_code)
);
GO

-- Create indexes for fast queries
CREATE NONCLUSTERED INDEX idx_date_route
    ON [dbo].[tbl_recommended_orders] (trx_date, route_code)
    INCLUDE (customer_code, item_code);
GO

CREATE NONCLUSTERED INDEX idx_customer
    ON [dbo].[tbl_recommended_orders] (customer_code, trx_date);
GO

CREATE NONCLUSTERED INDEX idx_item
    ON [dbo].[tbl_recommended_orders] (item_code, trx_date);
GO

CREATE NONCLUSTERED INDEX idx_generated_at
    ON [dbo].[tbl_recommended_orders] (generated_at DESC);
GO

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON [dbo].[tbl_recommended_orders] TO [your_app_user];
-- GO

PRINT 'All indexes created successfully!';
PRINT 'Table [tbl_recommended_orders] is ready to use.';
