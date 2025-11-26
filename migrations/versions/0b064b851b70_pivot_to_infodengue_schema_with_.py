
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0b064b851b70'
down_revision: Union[str, Sequence[str], None] = 'f6a5da26452d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    
    
    op.add_column('territories', sa.Column('geocode', sa.String(length=7), nullable=False))
    op.create_unique_constraint('uq_territories_geocode', 'territories', ['geocode'])
    op.create_table('weekly_reports',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('se', sa.Integer(), nullable=False, comment='Semana Epidemiológica (ex: 202544)'),
    sa.Column('geocode', sa.String(length=7), nullable=False),
    sa.Column('data_ini_se', sa.Date(), nullable=False, comment='Data de início da SE'),
    sa.Column('reported_cases', sa.Integer(), nullable=True),
    sa.Column('estimated_cases', sa.Float(), nullable=True),
    sa.Column('estimated_cases_min', sa.Integer(), nullable=True),
    sa.Column('estimated_cases_max', sa.Integer(), nullable=True),
    sa.Column('alert_level', sa.Integer(), nullable=True),
    sa.Column('population', sa.Float(), nullable=True),
    sa.Column('rt_value', sa.Float(), nullable=True),
    sa.Column('last_synced_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['geocode'], ['territories.geocode'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('geocode', 'se', name='uq_geocode_se_report')
    )
    op.create_index('idx_report_se_level', 'weekly_reports', ['se', 'alert_level'], unique=False)
    op.create_index(op.f('ix_weekly_reports_alert_level'), 'weekly_reports', ['alert_level'], unique=False)
    op.create_index(op.f('ix_weekly_reports_geocode'), 'weekly_reports', ['geocode'], unique=False)
    op.create_index(op.f('ix_weekly_reports_se'), 'weekly_reports', ['se'], unique=False)
    op.drop_index(op.f('idx_agg_state_year'), table_name='dengue_aggregates')
    op.drop_index(op.f('ix_dengue_aggregates_id_municip'), table_name='dengue_aggregates')
    op.drop_index(op.f('ix_dengue_aggregates_nu_ano'), table_name='dengue_aggregates')
    op.drop_index(op.f('ix_dengue_aggregates_sg_uf_not'), table_name='dengue_aggregates')
    op.drop_table('dengue_aggregates')
    op.drop_index(op.f('idx_territory_ibge_code'), table_name='territories')
    op.drop_index(op.f('ix_territories_ibge_code'), table_name='territories')
    op.drop_index(op.f('ix_territories_id_municip_sinan'), table_name='territories')
    op.drop_column('territories', 'id')
    op.drop_column('territories', 'ibge_code')
    op.drop_column('territories', 'id_municip_sinan')
    


def downgrade() -> None:
    
    
    op.add_column('territories', sa.Column('id_municip_sinan', sa.VARCHAR(length=10), autoincrement=False, nullable=False))
    op.add_column('territories', sa.Column('ibge_code', sa.VARCHAR(length=7), autoincrement=False, nullable=True))
    op.add_column('territories', sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False))
    op.create_index(op.f('ix_territories_id_municip_sinan'), 'territories', ['id_municip_sinan'], unique=True)
    op.create_index(op.f('ix_territories_ibge_code'), 'territories', ['ibge_code'], unique=True)
    op.create_index(op.f('idx_territory_ibge_code'), 'territories', ['ibge_code'], unique=False)
    op.drop_column('territories', 'geocode')
    op.create_table('dengue_aggregates',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('id_municip', sa.VARCHAR(length=10), autoincrement=False, nullable=False),
    sa.Column('nu_ano', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('sg_uf_not', sa.VARCHAR(length=2), autoincrement=False, nullable=True),
    sa.Column('cases_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('hospitalized_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('deaths_count', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('last_synced_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=False),
    sa.Column('source', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('dengue_aggregates_pkey')),
    sa.UniqueConstraint('id_municip', 'nu_ano', name=op.f('uq_municip_year_aggregate'), postgresql_include=[], postgresql_nulls_not_distinct=False)
    )
    op.create_index(op.f('ix_dengue_aggregates_sg_uf_not'), 'dengue_aggregates', ['sg_uf_not'], unique=False)
    op.create_index(op.f('ix_dengue_aggregates_nu_ano'), 'dengue_aggregates', ['nu_ano'], unique=False)
    op.create_index(op.f('ix_dengue_aggregates_id_municip'), 'dengue_aggregates', ['id_municip'], unique=False)
    op.create_index(op.f('idx_agg_state_year'), 'dengue_aggregates', ['sg_uf_not', 'nu_ano'], unique=False)
    op.drop_index(op.f('ix_weekly_reports_se'), table_name='weekly_reports')
    op.drop_index(op.f('ix_weekly_reports_geocode'), table_name='weekly_reports')
    op.drop_index(op.f('ix_weekly_reports_alert_level'), table_name='weekly_reports')
    op.drop_index('idx_report_se_level', table_name='weekly_reports')
    op.drop_table('weekly_reports')
    
