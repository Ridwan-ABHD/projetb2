# from datetime import datetime, timezone
# from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey
# from sqlalchemy.orm import relationship
# from database import Base


# class Hive(Base):
#     __tablename__ = "hives"

#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     location = Column(String, nullable=False)
#     status = Column(String, default="normal")  # normal | warning | critical

#     readings = relationship("SensorReading", back_populates="hive")
#     alerts = relationship("Alert", back_populates="hive")


# class SensorReading(Base):
#     __tablename__ = "sensor_readings"

#     id = Column(Integer, primary_key=True)
#     hive_id = Column(Integer, ForeignKey("hives.id"), nullable=False)
#     timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
#     frequency_hz = Column(Float, nullable=False)
#     temperature_c = Column(Float, nullable=False)
#     humidity_pct = Column(Float, nullable=False)
#     weight_kg = Column(Float, nullable=False)

#     hive = relationship("Hive", back_populates="readings")


# class Alert(Base):
#     __tablename__ = "alerts"

#     id = Column(Integer, primary_key=True)
#     hive_id = Column(Integer, ForeignKey("hives.id"), nullable=False)
#     timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
#     type = Column(String, nullable=False)  # SWARMING | DISEASE | THERMAL_STRESS | WEIGHT_DROP
#     message = Column(String, nullable=False)
#     severity = Column(String, nullable=False)  # info | warning | critical
#     is_resolved = Column(Boolean, default=False)

#     hive = relationship("Hive", back_populates="alerts")


# class Threshold(Base):
#     __tablename__ = "thresholds"

#     key = Column(String, primary_key=True)
#     value = Column(Float, nullable=False)
