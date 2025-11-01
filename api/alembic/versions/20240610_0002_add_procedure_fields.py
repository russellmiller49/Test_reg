"""add procedure type + details"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20240610_0002"
down_revision = "20240610_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "annotations",
        sa.Column("procedure_type", sa.Text(), nullable=False, server_default="EBUS"),
    )
    op.add_column(
        "annotations",
        sa.Column(
            "procedure_details",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.alter_column("annotations", "procedure_type", server_default=None)


def downgrade() -> None:
    op.drop_column("annotations", "procedure_details")
    op.drop_column("annotations", "procedure_type")
