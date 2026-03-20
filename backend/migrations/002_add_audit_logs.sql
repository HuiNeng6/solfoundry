-- Migration: Add audit_logs table with immutability trigger
-- This migration creates the audit log table with append-only enforcement

-- Create audit_logs table
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Who performed the action
    actor_id UUID,
    actor_type VARCHAR(50) NOT NULL DEFAULT 'user',
    actor_address VARCHAR(64),
    
    -- What action was performed
    action VARCHAR(50) NOT NULL,
    
    -- What was affected
    resource_type VARCHAR(50) NOT NULL,
    resource_id UUID,
    
    -- Context and details
    description TEXT NOT NULL,
    metadata JSONB,
    
    -- Request context for traceability
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    request_id VARCHAR(100),
    
    -- Related entities
    bounty_id UUID,
    pr_number VARCHAR(50),
    payment_id UUID,
    
    -- Timestamp (immutable)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_id ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource_id ON audit_logs(resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_bounty_id ON audit_logs(bounty_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS ix_audit_logs_request_id ON audit_logs(request_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_action ON audit_logs(actor_id, action);
CREATE INDEX IF NOT EXISTS ix_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS ix_audit_logs_action_time ON audit_logs(action, created_at);
CREATE INDEX IF NOT EXISTS ix_audit_logs_actor_time ON audit_logs(actor_id, created_at);

-- Create function to prevent updates and deletes on audit_logs
CREATE OR REPLACE FUNCTION enforce_audit_log_immutability()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce immutability (prevent UPDATE)
DROP TRIGGER IF EXISTS prevent_audit_log_update ON audit_logs;
CREATE TRIGGER prevent_audit_log_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION enforce_audit_log_immutability();

-- Create trigger to enforce immutability (prevent DELETE)
DROP TRIGGER IF EXISTS prevent_audit_log_delete ON audit_logs;
CREATE TRIGGER prevent_audit_log_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION enforce_audit_log_immutability();

-- Add comment to table
COMMENT ON TABLE audit_logs IS 'Immutable audit log table - records are append-only and cannot be modified or deleted';
COMMENT ON COLUMN audit_logs.actor_type IS 'Type of actor: user, system, or admin';
COMMENT ON COLUMN audit_logs.action IS 'Action type from AuditAction enum';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource: bounty, pr, payment, user, dispute, system';