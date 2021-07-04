"""general info

Revision ID: 3c0237a0b824
Revises: 7c6a29e1360d
Create Date: 2021-07-03 21:53:13.886239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c0237a0b824'
down_revision = '7c6a29e1360d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.add_column(sa.Column('LORs', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('call_schedule', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('categorical_positions', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('fellowships', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('preliminary_positions', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('program_director', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('program_type', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('research_required', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('social_media', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('step_1_cutoff', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('trauma_level', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('weeks_vacation', sa.String(length=500), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.drop_column('weeks_vacation')
        batch_op.drop_column('trauma_level')
        batch_op.drop_column('step_1_cutoff')
        batch_op.drop_column('social_media')
        batch_op.drop_column('research_required')
        batch_op.drop_column('program_type')
        batch_op.drop_column('program_director')
        batch_op.drop_column('preliminary_positions')
        batch_op.drop_column('fellowships')
        batch_op.drop_column('categorical_positions')
        batch_op.drop_column('call_schedule')
        batch_op.drop_column('LORs')

    # ### end Alembic commands ###