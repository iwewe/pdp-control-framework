-- PDP Control Framework - pgAudit setup
-- Run with appropriate administrative privileges after pgaudit is present
-- in shared_preload_libraries and PostgreSQL has been restarted.

CREATE EXTENSION IF NOT EXISTS pgaudit;

-- Verify configuration:
SHOW shared_preload_libraries;
SHOW pgaudit.log;
SHOW pgaudit.log_parameter;
SHOW pgaudit.log_statement;
SHOW pgaudit.log_rows;
