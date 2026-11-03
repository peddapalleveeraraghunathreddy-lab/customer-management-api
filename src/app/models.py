from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    city = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())