"""add created_at

Revision ID: 8c9494b88fa7
Revises: 40dbff788d66
Create Date: 2026-03-23 18:24:48.899874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c9494b88fa7'
down_revision: Union[str, Sequence[str], None] = '40dbff788d66'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE")

def downgrade():
    op.execute("ALTER TABLE tasks DROP COLUMN IF EXISTS created_at")
