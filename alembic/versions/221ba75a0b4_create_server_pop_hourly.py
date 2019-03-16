"""create server_pop_hourly

Revision ID: 221ba75a0b4
Revises: 
Create Date: 2019-03-15 21:12:24.385000

"""

# revision identifiers, used by Alembic.
revision = '221ba75a0b4'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'server_pop_hourly',
        sa.Column('server',
                  sa.BigInteger,
                  primary_key=True,
                  nullable=False),
        sa.Column('datetime',
                  sa.DateTime,
                  primary_key=True,
                  nullable=False),
        sa.Column('user_count',
                  sa.Integer,
                  nullable=False)
    )


def downgrade():
    op.drop_table('server_pop_hourly')
