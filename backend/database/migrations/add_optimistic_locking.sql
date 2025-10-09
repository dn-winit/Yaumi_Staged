-- Migration: Add optimistic locking to supervision tables
-- Date: 2025-01-10
-- Purpose: Prevent concurrent user data loss with version control

-- Add record_version column to route summary table
ALTER TABLE [YaumiAIML].[dbo].[tbl_supervision_route_summary]
ADD record_version INT NOT NULL DEFAULT 1;

GO

-- Add indexes for performance
CREATE INDEX idx_route_session_version
ON [YaumiAIML].[dbo].[tbl_supervision_route_summary](session_id, record_version);

GO

-- Add comments for documentation
EXEC sp_addextendedproperty
    @name = N'MS_Description',
    @value = N'Version number for optimistic locking. Incremented on each update to detect concurrent modifications.',
    @level0type = N'SCHEMA', @level0name = N'dbo',
    @level1type = N'TABLE', @level1name = N'tbl_supervision_route_summary',
    @level2type = N'COLUMN', @level2name = N'record_version';

GO

-- Test query to verify
SELECT TOP 1
    session_id,
    route_code,
    supervision_date,
    record_version,
    record_created_at
FROM [YaumiAIML].[dbo].[tbl_supervision_route_summary]
ORDER BY record_created_at DESC;

GO

PRINT 'Migration completed successfully. Optimistic locking enabled for supervision sessions.';
