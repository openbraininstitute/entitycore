"""Add ScientificArtifact table

Revision ID: a1b2c3d4e5f6
Revises: b74f3ebacbca
Create Date: 2025-05-01 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None  # Replace with the previous revision ID
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'scientific_artifact',
        sa.Column('id', postgresql.UUID(as_uuid=True), sa.ForeignKey('entity.id'), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('legacy_id', postgresql.ARRAY(sa.String), default=list),
        sa.Column('legacy_self', postgresql.ARRAY(sa.String), default=list),
        sa.Column('creation_date', sa.DateTime, default=datetime.utcnow, nullable=False),
        sa.Column('update_date', sa.DateTime, default=datetime.utcnow, nullable=False),
        sa.Column('authorized_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('authorized_public', sa.Boolean, default=False),
        sa.Column('license_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('license.id'), nullable=True),
    )

def downgrade():
    op.drop_table('scientific_artifact')
