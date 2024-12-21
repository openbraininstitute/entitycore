from sqlalchemy.orm import mapped_column, Mapped

from app.models.base import Base, LegacyMixin, TimestampMixin


class Role(LegacyMixin, TimestampMixin, Base):
    __tablename__ = "role"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    role_id: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
