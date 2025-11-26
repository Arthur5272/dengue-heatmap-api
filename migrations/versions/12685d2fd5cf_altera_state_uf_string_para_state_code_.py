
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '12685d2fd5cf'
down_revision: Union[str, Sequence[str], None] = '0b064b851b70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    
    op.add_column('territories', sa.Column('state_code', sa.Integer(), nullable=False))
    op.drop_index(op.f('ix_territories_state_uf'), table_name='territories')
    op.execute("ALTER TABLE territories DROP CONSTRAINT uq_territories_geocode CASCADE")
    op.create_index(op.f('ix_territories_state_code'), 'territories', ['state_code'], unique=False)
    op.drop_column('territories', 'state_uf')
    op.create_unique_constraint(op.f('uq_territories_geocode'), 'territories', ['geocode'], postgresql_nulls_not_distinct=False)
    op.create_foreign_key('weekly_reports_geocode_fkey', 'weekly_reports', 'territories', ['geocode'], ['geocode'])
    


def downgrade() -> None:
    
    
    op.add_column('territories', sa.Column('state_uf', sa.VARCHAR(length=2), autoincrement=False, nullable=False))
    op.drop_index(op.f('ix_territories_state_code'), table_name='territories')
    op.drop_constraint('weekly_reports_geocode_fkey', 'weekly_reports', type_='foreignkey')
    op.create_unique_constraint(op.f('uq_territories_geocode'), 'territories', ['geocode'], postgresql_nulls_not_distinct=False)
    op.create_index(op.f('ix_territories_state_uf'), 'territories', ['state_uf'], unique=False)
    op.drop_column('territories', 'state_code')
    
