"""Create event_teachers association table

Revision ID: bac3ec7e9f54
Revises: 99f8100c3b5d
Create Date: 2025-10-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bac3ec7e9f54'
down_revision = '99f8100c3b5d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'event_teachers',
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.event_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.teacher_id'], ondelete='CASCADE', onupdate='CASCADE'),
        sa.PrimaryKeyConstraint('event_id', 'teacher_id'),
    )


def downgrade() -> None:
    op.drop_table('event_teachers')
