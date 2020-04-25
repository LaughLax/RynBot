"""Add mute role column to server config table

Revision ID: 5f1cf30db9e0
Revises: 16735f2348ae
Create Date: 2020-04-23 22:44:20.738681

"""

# revision identifiers, used by Alembic.
revision = '5f1cf30db9e0'
down_revision = '16735f2348ae'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('server_config', sa.Column('mute_role', sa.BigInteger(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('server_config', 'mute_role')
    # ### end Alembic commands ###