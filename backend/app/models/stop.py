import enum

from sqlalchemy import Column, Integer, String, Float, Time, Enum

from app.database import Base


class StopStatus(str, enum.Enum):
    PENDING = "pending"
    IN_ROUTE = "in_route"
    DELIVERED = "delivered"
    FAILED = "failed"


class Stop(Base):
    __tablename__ = "stops"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    earliest_time = Column(Time, nullable=False)
    latest_time = Column(Time, nullable=False)
    package_weight_kg = Column(Float, nullable=False)
    status = Column(Enum(StopStatus), default=StopStatus.PENDING, nullable=False)
