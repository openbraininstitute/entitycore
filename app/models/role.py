from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import mapped_column

from app.models.base import Base, LegacyMixin, TimestampMixin


class Role(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "role"
    id = mapped_column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    role_id = Column(String, unique=True, index=True, nullable=False)
