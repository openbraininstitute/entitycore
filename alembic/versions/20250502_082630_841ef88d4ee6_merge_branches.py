"""Merge branches

Revision ID: 841ef88d4ee6
Revises: 7458f8ff53f0
Create Date: 2025-05-02 08:26:30.632969

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "841ef88d4ee6"
down_revision: str | None = "7458f8ff53f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
