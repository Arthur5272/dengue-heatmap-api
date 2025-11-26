import datetime
from sqlalchemy import (
    Integer, String, DateTime, Index, Float, Date
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint, ForeignKey
from typing import List

class Base(DeclarativeBase):
    pass

class Territory(Base):
    
    __tablename__ = "territories"

    
    geocode: Mapped[str] = mapped_column(String(7), primary_key=True)
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    state_code: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    
    
    reports: Mapped[List["WeeklyReport"]] = relationship(back_populates="territory")


class WeeklyReport(Base):
    
    __tablename__ = "weekly_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    
    se: Mapped[int] = mapped_column(Integer, nullable=False, index=True, 
                                   comment="Semana Epidemiológica (ex: 202544)")
    
    
    geocode: Mapped[str] = mapped_column(
        String(7), 
        ForeignKey("territories.geocode"), 
        nullable=False, 
        index=True
    )

    
    
    territory: Mapped["Territory"] = relationship(back_populates="reports")

    
    data_ini_se: Mapped[datetime.date] = mapped_column(Date, nullable=False,
                                                     comment="Data de início da SE")
    
    
    reported_cases: Mapped[int] = mapped_column(Integer, nullable=True)
    
    
    estimated_cases: Mapped[float] = mapped_column(Float, nullable=True)
    estimated_cases_min: Mapped[int] = mapped_column(Integer, nullable=True)
    estimated_cases_max: Mapped[int] = mapped_column(Integer, nullable=True)

    
    alert_level: Mapped[int] = mapped_column(Integer, nullable=True, index=True)
    
    
    population: Mapped[float] = mapped_column(Float, nullable=True)
    
    
    rt_value: Mapped[float] = mapped_column(Float, nullable=True)

    
    last_synced_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        
        UniqueConstraint("geocode", "se", name="uq_geocode_se_report"),
        Index("idx_report_se_level", "se", "alert_level"),
    )