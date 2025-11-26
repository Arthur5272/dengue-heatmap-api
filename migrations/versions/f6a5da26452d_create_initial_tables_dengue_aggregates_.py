
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'f6a5da26452d'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    
    op.create_table('dengue_aggregates',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_municip', sa.String(length=10), nullable=False),
    sa.Column('nu_ano', sa.Integer(), nullable=False),
    sa.Column('sg_uf_not', sa.String(length=2), nullable=True),
    sa.Column('cases_count', sa.Integer(), nullable=False),
    sa.Column('hospitalized_count', sa.Integer(), nullable=False),
    sa.Column('deaths_count', sa.Integer(), nullable=False),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('source', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id_municip', 'nu_ano', name='uq_municip_year_aggregate')
    )
    op.create_index('idx_agg_state_year', 'dengue_aggregates', ['sg_uf_not', 'nu_ano'], unique=False)
    op.create_index(op.f('ix_dengue_aggregates_id_municip'), 'dengue_aggregates', ['id_municip'], unique=False)
    op.create_index(op.f('ix_dengue_aggregates_nu_ano'), 'dengue_aggregates', ['nu_ano'], unique=False)
    op.create_index(op.f('ix_dengue_aggregates_sg_uf_not'), 'dengue_aggregates', ['sg_uf_not'], unique=False)
    op.create_table('territories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('id_municip_sinan', sa.String(length=10), nullable=False),
    sa.Column('ibge_code', sa.String(length=7), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('state_uf', sa.String(length=2), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_territory_ibge_code', 'territories', ['ibge_code'], unique=False)
    op.create_index(op.f('ix_territories_ibge_code'), 'territories', ['ibge_code'], unique=True)
    op.create_index(op.f('ix_territories_id_municip_sinan'), 'territories', ['id_municip_sinan'], unique=True)
    op.create_index(op.f('ix_territories_state_uf'), 'territories', ['state_uf'], unique=False)
    


def downgrade() -> None:
    
    
    op.drop_index(op.f('ix_territories_state_uf'), table_name='territories')
    op.drop_index(op.f('ix_territories_id_municip_sinan'), table_name='territories')
    op.drop_index(op.f('ix_territories_ibge_code'), table_name='territories')
    op.drop_index('idx_territory_ibge_code', table_name='territories')
    op.drop_table('territories')
    op.drop_index(op.f('ix_dengue_aggregates_sg_uf_not'), table_name='dengue_aggregates')
    op.drop_index(op.f('ix_dengue_aggregates_nu_ano'), table_name='dengue_aggregates')
    op.drop_index(op.f('ix_dengue_aggregates_id_municip'), table_name='dengue_aggregates')
    op.drop_index('idx_agg_state_year', table_name='dengue_aggregates')
    op.drop_table('dengue_aggregates')
    
