

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class TerritoryBase(BaseModel):
    geocode: str
    name: str
    state_code: int

class TerritoryPublic(TerritoryBase):
    class Config:
        from_attributes = True


class WeeklyReportBase(BaseModel):
    se: int
    data_ini_se: date
    reported_cases: Optional[int] = 0
    estimated_cases: Optional[float] = 0
    alert_level: Optional[int] = None
    population: Optional[float] = None
    rt_value: Optional[float] = None

class WeeklyReportPublic(WeeklyReportBase):
    id: int
    geocode: str
    last_synced_at: datetime
    
    
    territory: Optional[TerritoryPublic] = None

    class Config:
        from_attributes = True


class StateAggregation(BaseModel):
    state_code: int
    total_cases: int
    avg_alert_level: float
    total_population: float
    report_count: int 

    class Config:
        from_attributes = True