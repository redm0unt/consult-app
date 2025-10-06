"""Add name, consultations count, and duration to events

Revision ID: 7f9d4c1b2a34
Revises: d8a36078f50a
Create Date: 2025-10-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7f9d4c1b2a34'
down_revision = 'd8a36078f50a'
branch_labels = None
depends_on = None


DEFAULT_EVENT_NAME = 'Мероприятие'


def upgrade() -> None:
    op.add_column('events', sa.Column('name', sa.String(length=120), nullable=False, server_default=DEFAULT_EVENT_NAME))
    op.add_column('events', sa.Column('consultations_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column(
        'events',
        sa.Column(
            'duration_minutes',
            sa.Integer(),
            sa.Computed('TIMESTAMPDIFF(MINUTE, start_time, end_time)'),
            nullable=True,
        ),
    )

    # drop server default after applying to existing rows
    op.alter_column('events', 'name', server_default=None)
    op.alter_column('events', 'consultations_count', server_default=None)


def downgrade() -> None:
    op.drop_column('events', 'duration_minutes')
    op.drop_column('events', 'consultations_count')
    op.drop_column('events', 'name')
