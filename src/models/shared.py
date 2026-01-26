from datetime import datetime, UTC

from sqlalchemy import Column, Integer, DateTime

from src.db.database import Base


class EntityBase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime(timezone=True),
                        default=lambda: datetime.now(UTC),
                        onupdate=lambda: datetime.now(UTC))
