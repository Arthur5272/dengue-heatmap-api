import datetime
from sqlalchemy import (
    Integer, String, DateTime, Index, Float, Date
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint, ForeignKey

class Base(DeclarativeBase):
    pass

class Territory(Base):
    """
    Tabela de 'lookup' para municípios.
    Armazena o código IBGE (geocode) como chave principal.
    """
    __tablename__ = "territories"

    # Geocode (IBGE 7 dígitos) é nossa chave primária de negócios
    geocode: Mapped[str] = mapped_column(String(7), primary_key=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)


class WeeklyReport(Base):
    """
    Modelo para armazenar os dados semanais agregados do InfoDengue.
    """
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Chave de agregação (Semana Epidemiológica)
    se: Mapped[int] = mapped_column(Integer, nullable=False, index=True, 
                                   comment="Semana Epidemiológica (ex: 202544)")
    
    # Chave de Localização (FK para a tabela Territory)
    geocode: Mapped[str] = mapped_column(
        String(7), 
        ForeignKey("territories.geocode"), 
        nullable=False, 
        index=True
    )

    # --- Métricas do InfoDengue ---
    data_ini_se: Mapped[datetime.date] = mapped_column(Date, nullable=False,
                                                     comment="Data de início da SE")
    
    # 'casos' (reportados)
    reported_cases: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # 'casos_est' (estimados)
    estimated_cases: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_cases_min: Mapped[int] = mapped_column(Integer, nullable=True)
    estimated_cases_max: Mapped[int] = mapped_column(Integer, nullable=True)

    # 'nivel' (Nível de Alerta: 1-Verde, 2-Amarelo, 3-Laranja, 4-Vermelho)
    alert_level: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    
    # 'pop' (População)
    population: Mapped[float] = mapped_column(Float, nullable=True)
    
    # 'Rt' (Número de reprodução)
    rt_value: Mapped[float] = mapped_column(Float, nullable=True)

    # --- Metadados de Sincronização ---
    last_synced_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        # Garante que só temos uma entrada por município/semana
        UniqueConstraint("geocode", "se", name="uq_geocode_se_report"),
        Index("idx_report_se_level", "se", "alert_level"),
    )