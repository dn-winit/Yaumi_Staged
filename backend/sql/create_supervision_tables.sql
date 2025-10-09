-- =====================================================
-- SALES SUPERVISION SYSTEM - TABLE CREATION SCRIPT
-- Database: YaumiAIML
-- Author: WINIT Analytics Team
-- Created: 2025-10-09
-- =====================================================

USE [YaumiAIML]
GO

-- =====================================================
-- Table 1: Route Summary (Master)
-- Purpose: Session-level aggregated metrics
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[tbl_supervision_route_summary]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[tbl_supervision_route_summary] (
        -- Primary Key
        route_summary_id INT IDENTITY(1,1) PRIMARY KEY,

        -- Session Identity
        session_id VARCHAR(100) NOT NULL UNIQUE,
        route_code VARCHAR(50) NOT NULL,
        supervision_date DATE NOT NULL,

        -- Customer Coverage Metrics
        total_customers_planned INT NOT NULL,
        total_customers_visited INT NOT NULL,
        customer_completion_rate DECIMAL(5,2) NOT NULL,

        -- SKU Coverage Metrics
        total_skus_recommended INT NOT NULL,
        total_skus_sold INT NOT NULL,
        sku_coverage_rate DECIMAL(5,2) NOT NULL,

        -- Quantity Performance Metrics
        total_qty_recommended INT NOT NULL,
        total_qty_actual INT NOT NULL,
        qty_fulfillment_rate DECIMAL(5,2) NOT NULL,

        -- Redistribution Metrics
        redistribution_count INT DEFAULT 0,
        redistribution_qty INT DEFAULT 0,

        -- Overall Performance
        route_performance_score DECIMAL(5,2) NOT NULL,

        -- AI Analysis
        llm_performance_analysis TEXT,

        -- Session Status
        session_status VARCHAR(20) DEFAULT 'active',

        -- Timestamps
        session_started_at DATETIME DEFAULT GETDATE(),
        session_completed_at DATETIME,

        -- Indexes
        CONSTRAINT idx_route_date UNIQUE (route_code, supervision_date),
        INDEX idx_session (session_id),
        INDEX idx_status (session_status)
    )

    PRINT 'Table [tbl_supervision_route_summary] created successfully'
END
ELSE
BEGIN
    PRINT 'Table [tbl_supervision_route_summary] already exists'
END
GO

-- =====================================================
-- Table 2: Customer Summary (Visited Only)
-- Purpose: Customer-level performance tracking
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[tbl_supervision_customer_summary]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[tbl_supervision_customer_summary] (
        -- Primary Key
        customer_summary_id INT IDENTITY(1,1) PRIMARY KEY,

        -- Foreign Key
        session_id VARCHAR(100) NOT NULL,
        customer_code VARCHAR(50) NOT NULL,

        -- Visit Tracking
        visit_sequence SMALLINT NOT NULL,
        visit_timestamp DATETIME NOT NULL,

        -- SKU Coverage Metrics
        total_skus_recommended INT NOT NULL,
        total_skus_sold INT NOT NULL,
        sku_coverage_rate DECIMAL(5,2) NOT NULL,

        -- Quantity Performance Metrics
        total_qty_recommended INT NOT NULL,
        total_qty_actual INT NOT NULL,
        qty_fulfillment_rate DECIMAL(5,2) NOT NULL,

        -- Performance Score
        customer_performance_score DECIMAL(5,2) NOT NULL,

        -- AI Analysis
        llm_performance_analysis TEXT,

        -- Timestamp
        record_saved_at DATETIME DEFAULT GETDATE(),

        -- Constraints & Indexes
        CONSTRAINT UQ_session_customer UNIQUE (session_id, customer_code),
        CONSTRAINT FK_customer_route FOREIGN KEY (session_id)
            REFERENCES tbl_supervision_route_summary(session_id) ON DELETE CASCADE,
        INDEX idx_session (session_id),
        INDEX idx_customer (customer_code),
        INDEX idx_visit_order (session_id, visit_sequence),
        INDEX idx_performance (customer_performance_score)
    )

    PRINT 'Table [tbl_supervision_customer_summary] created successfully'
END
ELSE
BEGIN
    PRINT 'Table [tbl_supervision_customer_summary] already exists'
END
GO

-- =====================================================
-- Table 3: Item Details (Transactional)
-- Purpose: Item-level actual vs recommended tracking
-- =====================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[tbl_supervision_item_details]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[tbl_supervision_item_details] (
        -- Primary Key
        item_detail_id INT IDENTITY(1,1) PRIMARY KEY,

        -- Foreign Keys
        session_id VARCHAR(100) NOT NULL,
        customer_code VARCHAR(50) NOT NULL,
        item_code VARCHAR(50) NOT NULL,
        item_name VARCHAR(200) NOT NULL,

        -- Recommendation Tracking
        original_recommended_qty INT NOT NULL,
        adjusted_recommended_qty INT NOT NULL,
        recommendation_adjustment INT DEFAULT 0,

        -- Actual Tracking
        original_actual_qty INT NOT NULL,
        final_actual_qty INT NOT NULL,
        actual_adjustment INT DEFAULT 0,

        -- Status Flags
        was_manually_edited BIT DEFAULT 0,
        was_item_sold BIT NOT NULL,

        -- Planning Context (Snapshot)
        recommendation_tier VARCHAR(50) NOT NULL,
        priority_score DECIMAL(10,2) NOT NULL,
        van_inventory_qty INT NOT NULL,
        days_since_last_purchase INT NOT NULL,
        purchase_cycle_days DECIMAL(10,2) NOT NULL,
        purchase_frequency_pct DECIMAL(5,2) NOT NULL,

        -- Timestamps
        visit_timestamp DATETIME NOT NULL,
        record_saved_at DATETIME DEFAULT GETDATE(),

        -- Constraints & Indexes
        CONSTRAINT UQ_session_customer_item UNIQUE (session_id, customer_code, item_code),
        INDEX idx_session (session_id),
        INDEX idx_customer (customer_code),
        INDEX idx_item (item_code),
        INDEX idx_sold (was_item_sold)
    )

    PRINT 'Table [tbl_supervision_item_details] created successfully'
END
ELSE
BEGIN
    PRINT 'Table [tbl_supervision_item_details] already exists'
END
GO

-- =====================================================
-- Verification Query
-- =====================================================
PRINT ''
PRINT '============================================='
PRINT 'SUPERVISION TABLES CREATED SUCCESSFULLY'
PRINT '============================================='
PRINT ''

SELECT
    'tbl_supervision_route_summary' as TableName,
    COUNT(*) as ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'tbl_supervision_route_summary'

UNION ALL

SELECT
    'tbl_supervision_customer_summary' as TableName,
    COUNT(*) as ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'tbl_supervision_customer_summary'

UNION ALL

SELECT
    'tbl_supervision_item_details' as TableName,
    COUNT(*) as ColumnCount
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'tbl_supervision_item_details'

GO

PRINT 'Script execution completed!'
