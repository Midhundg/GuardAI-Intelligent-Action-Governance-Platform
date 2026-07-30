"""initial_schema_indexes_constraints

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-07-30

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ensure Indexes on high cardinality columns for performance
    op.create_index('ix_users_username_is_deleted', 'users', ['username', 'is_deleted'], if_not_exists=True)
    op.create_index('ix_policies_action_enabled', 'policies', ['action', 'enabled', 'is_deleted'], if_not_exists=True)
    op.create_index('ix_audit_logs_request_action', 'audit_logs', ['request_id', 'action'], if_not_exists=True)
    op.create_index('ix_approval_requests_status_expires', 'approval_requests', ['status', 'expires_at'], if_not_exists=True)
    op.create_index('ix_llm_cost_logs_provider_created', 'llm_cost_logs', ['provider', 'created_at'], if_not_exists=True)


def downgrade() -> None:
    op.drop_index('ix_llm_cost_logs_provider_created', table_name='llm_cost_logs', if_exists=True)
    op.drop_index('ix_approval_requests_status_expires', table_name='approval_requests', if_exists=True)
    op.drop_index('ix_audit_logs_request_action', table_name='audit_logs', if_exists=True)
    op.drop_index('ix_policies_action_enabled', table_name='policies', if_exists=True)
    op.drop_index('ix_users_username_is_deleted', table_name='users', if_exists=True)
