"""Optimize indexes and integrity constraints per Supabase Postgres guidelines.

Revision ID: 002_optimize_indexes_and_constraints
Revises: 001_initial_schema
Create Date: 2026-10-09 20:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_optimized_indexes'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Foreign Key Indexes (Eliminates Seq Scans on JOINs and Cascades)
    op.create_index(
        'idx_call_tasks_student_id',
        'call_tasks',
        ['student_id'],
        unique=False,
    )
    op.create_index(
        'idx_call_tasks_script_id',
        'call_tasks',
        ['script_id'],
        unique=False,
    )
    op.create_index(
        'idx_call_campaigns_script_id',
        'call_campaigns',
        ['script_id'],
        unique=False,
    )
    op.create_index(
        'idx_call_campaigns_created_by',
        'call_campaigns',
        ['created_by'],
        unique=False,
    )
    op.create_index(
        'idx_call_scripts_created_by',
        'call_scripts',
        ['created_by'],
        unique=False,
    )

    # 2. High-Throughput Partial Index for Celery Dispatcher (100x faster polling)
    op.create_index(
        'idx_call_tasks_pending_scheduled',
        'call_tasks',
        ['scheduled_at'],
        unique=False,
        postgresql_where=sa.text("status = 'pending'"),
    )

    # 3. Composite Indexes for Dashboard Filtering & Student Segmentation
    op.create_index(
        'idx_call_tasks_campaign_status',
        'call_tasks',
        ['campaign_id', 'status'],
        unique=False,
    )
    op.create_index(
        'idx_students_dept_sem_active',
        'students',
        ['department', 'semester', 'is_active'],
        unique=False,
    )

    # 4. Check Constraints for Schema Domain Integrity
    op.create_check_constraint(
        'ck_call_tasks_status',
        'call_tasks',
        "status IN ('pending', 'ringing', 'in_progress', 'completed', 'failed', 'busy', 'no_answer', 'voicemail')",
    )
    op.create_check_constraint(
        'ck_call_campaigns_status',
        'call_campaigns',
        "status IN ('pending', 'running', 'paused', 'completed', 'cancelled')",
    )
    op.create_check_constraint(
        'ck_students_semester',
        'students',
        "semester IS NULL OR (semester >= 1 AND semester <= 8)",
    )
    op.create_check_constraint(
        'ck_students_language_pref',
        'students',
        "language_pref IN ('hi', 'gu', 'en')",
    )


def downgrade() -> None:
    # 4. Drop Check Constraints
    op.drop_constraint('ck_students_language_pref', 'students', type_='check')
    op.drop_constraint('ck_students_semester', 'students', type_='check')
    op.drop_constraint('ck_call_campaigns_status', 'call_campaigns', type_='check')
    op.drop_constraint('ck_call_tasks_status', 'call_tasks', type_='check')

    # 3. Drop Composite Indexes
    op.drop_index('idx_students_dept_sem_active', table_name='students')
    op.drop_index('idx_call_tasks_campaign_status', table_name='call_tasks')

    # 2. Drop Partial Index
    op.drop_index('idx_call_tasks_pending_scheduled', table_name='call_tasks')

    # 1. Drop Foreign Key Indexes
    op.drop_index('idx_call_scripts_created_by', table_name='call_scripts')
    op.drop_index('idx_call_campaigns_created_by', table_name='call_campaigns')
    op.drop_index('idx_call_campaigns_script_id', table_name='call_campaigns')
    op.drop_index('idx_call_tasks_script_id', table_name='call_tasks')
    op.drop_index('idx_call_tasks_student_id', table_name='call_tasks')
