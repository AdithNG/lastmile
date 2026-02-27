from sqlalchemy import Column, Integer, Float, Date, ForeignKey, String
from sqlalchemy.orm import relationship

from app.database import Base


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_distance_km = Column(Float, default=0.0)
    total_time_min = Column(Float, default=0.0)

    vehicle = relationship("Vehicle")
    route_stops = relationship("RouteStop", back_populates="route", order_by="RouteStop.sequence")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    stop_id = Column(Integer, ForeignKey("stops.id"), nullable=False)
    sequence = Column(Integer, nullable=False)
    planned_arrival = Column(String, nullable=True)   # "HH:MM" string
    actual_arrival = Column(String, nullable=True)

    route = relationship("Route", back_populates="route_stops")
    stop = relationship("Stop")
