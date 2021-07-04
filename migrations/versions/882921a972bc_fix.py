"""fix

Revision ID: 882921a972bc
Revises: 156a9925f575
Create Date: 2021-07-03 22:35:59.702714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '882921a972bc'
down_revision = '156a9925f575'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.alter_column('trauma_level',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=500),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('program', schema=None) as batch_op:
        batch_op.alter_column('trauma_level',
               existing_type=sa.String(length=500),
               type_=sa.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###
