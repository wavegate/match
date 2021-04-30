"""empty message

Revision ID: df9ef8a790d1
Revises: 29910811f4c8
Create Date: 2021-04-29 22:58:12.634833

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'df9ef8a790d1'
down_revision = '29910811f4c8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.TEXT(),
               type_=sa.String(length=300),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.String(length=300),
               type_=sa.TEXT(),
               existing_nullable=True)

    # ### end Alembic commands ###
