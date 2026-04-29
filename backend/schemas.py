# from datetime import datetime
# from typing import List, Optional
# from pydantic import BaseModel


# class SensorReadingOut(BaseModel):
#     id: int
#     hive_id: int
#     timestamp: datetime
#     frequency_hz: float
#     temperature_c: float
#     humidity_pct: float
#     weight_kg: float

#     model_config = {"from_attributes": True}


# class AlertOut(BaseModel):
#     id: int
#     hive_id: int
#     timestamp: datetime
#     type: str
#     message: str
#     severity: str
#     is_resolved: bool

#     model_config = {"from_attributes": True}


# class HiveOut(BaseModel):
#     id: int
#     name: str
#     location: str
#     status: str
#     last_reading: Optional[SensorReadingOut] = None
#     active_alerts: List[AlertOut] = []

#     model_config = {"from_attributes": True}


# class ThresholdUpdate(BaseModel):
#     freq_warning: float = 260.0
#     freq_critical: float = 280.0
#     temp_warning: float = 36.0
#     temp_critical: float = 38.0
#     humidity_min: float = 50.0
#     humidity_max: float = 80.0
#     weight_drop_threshold: float = 2.0


# class DiagnosisRequest(BaseModel):
#     hive_id: int
#     duration_seconds: int = 30


# class DiagnosisResult(BaseModel):
#     hive_id: int
#     hive_name: str
#     swarming_probability: float
#     dominant_frequency: float
#     stress_level: str
#     duration_seconds: int
#     recommendation: str
