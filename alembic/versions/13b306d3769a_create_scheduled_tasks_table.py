"""create_scheduled_tasks_table

Revision ID: 13b306d3769a
Revises: 85ffec7736c0
Create Date: 2019-10-13 21:17:52.821699

"""

# revision identifiers, used by Alembic.
revision = '13b306d3769a'
down_revision = '85ffec7736c0'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scheduled_tasks',
    sa.Column('server', sa.BigInteger(), nullable=False),
    sa.Column('channel', sa.BigInteger(), nullable=False),
    sa.Column('task_name', sa.String(length=32), nullable=False),
    sa.Column('command', sa.String(length=32), nullable=False),
    sa.Column('last_run_msg_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['server'], ['server_config.server'], ),
    sa.PrimaryKeyConstraint('server', 'task_name'),
    sa.UniqueConstraint('last_run_msg_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('scheduled_tasks')
    # ### end Alembic commands ###
