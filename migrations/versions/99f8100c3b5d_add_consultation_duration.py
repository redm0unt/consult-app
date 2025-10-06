"""Add consultation duration minutes to events

Revision ID: 99f8100c3b5d
Revises: 7f9d4c1b2a34
Create Date: 2025-10-06 00:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99f8100c3b5d'
down_revision = '7f9d4c1b2a34'
branch_labels = None
depends_on = None

DEFAULT_DURATION = 15


def upgrade() -> None:
    op.add_column(
        'events',
        sa.Column(
            'consultation_duration_minutes',
            sa.Integer(),
            nullable=False,
            server_default=str(DEFAULT_DURATION),
        ),
    )
    op.alter_column('events', 'consultation_duration_minutes', server_default=None)


def downgrade() -> None:
    op.drop_column('events', 'consultation_duration_minutes')
