"""Base model for all database models."""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all database models."""

    # Common columns for all models
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        attrs = []
        for key in self.__mapper__.columns.keys():
            if not key.startswith("_"):
                value = getattr(self, key)
                attrs.append(f"{key}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary.

        Returns:
            A dictionary representation of the model.
        """
        result = {}
        for key in self.__mapper__.columns.keys():
            if not key.startswith("_"):
                value = getattr(self, key)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[key] = value
        return result
