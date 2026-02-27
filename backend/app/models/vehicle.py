from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    depot_id = Column(Integer, ForeignKey("depots.id"), nullable=False)
    capacity_kg = Column(Float, nullable=False)
    driver_name = Column(String, nullable=False)

    depot = relationship("Depot")
