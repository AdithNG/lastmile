from sqlalchemy import Column, Integer, String, Float, Time

from app.database import Base


class Depot(Base):
    __tablename__ = "depots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    open_time = Column(Time, nullable=False)
    close_time = Column(Time, nullable=False)
