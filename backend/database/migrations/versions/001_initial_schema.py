"""Initial schema migration: staff_users, students, call_scripts, call_campaigns, call_tasks, call_logs

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-09 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Staff Users
    op.create_table(
        'staff_users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('role', sa.String(length=20), server_default='operator', nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_staff_users_email'), 'staff_users', ['email'], unique=True)

    # 2. Students
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('roll_number', sa.String(length=20), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=15), nullable=False),
        sa.Column('alt_phone', sa.String(length=15), nullable=True),
        sa.Column('language_pref', sa.String(length=10), server_default='hi', nullable=False),
        sa.Column('department', sa.String(length=50), nullable=True),
        sa.Column('semester', sa.Integer(), nullable=True),
        sa.Column('whatsapp_number', sa.String(length=15), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_students_roll_number'), 'students', ['roll_number'], unique=True)
    op.create_index(op.f('ix_students_phone'), 'students', ['phone'], unique=False)

    # 3. Call Scripts
    op.create_table(
        'call_scripts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('opening_message', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_scripts_category'), 'call_scripts', ['category'], unique=False)

    # 4. Call Campaigns
    op.create_table(
        'call_campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('script_id', sa.Integer(), nullable=False),
        sa.Column('target_filter', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_retries', sa.Integer(), server_default='2', nullable=False),
        sa.Column('retry_delay_min', sa.Integer(), server_default='60', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['staff_users.id'], ),
        sa.ForeignKeyConstraint(['script_id'], ['call_scripts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_call_campaigns_scheduled_at'), 'call_campaigns', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_call_campaigns_status'), 'call_campaigns', ['status'], unique=False)

    # 5. Call Tasks
    op.create_table(
        'call_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('student_phone', sa.String(length=15), nullable=False),
        sa.Column('script_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('plivo_uuid', sa.String(length=50), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('placed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('answered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ended_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_sec', sa.Integer(), nullable=True),
        sa.Column('outcome', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['call_campaigns.id'], ),
        sa.ForeignKeyConstraint(['script_id'], ['call_scripts.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_call_tasks_campaign', 'call_tasks', ['campaign_id'], unique=False)
    op.create_index('idx_call_tasks_scheduled', 'call_tasks', ['scheduled_at'], unique=False)
    op.create_index('idx_call_tasks_status', 'call_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_call_tasks_plivo_uuid'), 'call_tasks', ['plivo_uuid'], unique=False)

    # 6. Call Logs
    op.create_table(
        'call_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('transcript', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('stt_provider', sa.String(length=20), nullable=True),
        sa.Column('llm_provider', sa.String(length=20), nullable=True),
        sa.Column('tts_provider', sa.String(length=20), nullable=True),
        sa.Column('avg_latency_ms', sa.Integer(), nullable=True),
        sa.Column('max_latency_ms', sa.Integer(), nullable=True),
        sa.Column('error_log', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['task_id'], ['call_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_call_logs_task', 'call_logs', ['task_id'], unique=True)


def downgrade() -> None:
    op.drop_table('call_logs')
    op.drop_table('call_tasks')
    op.drop_table('call_campaigns')
    op.drop_table('call_scripts')
    op.drop_table('students')
    op.drop_table('staff_users')
