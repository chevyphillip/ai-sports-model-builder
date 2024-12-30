"""Tests for the base model."""

from datetime import datetime
from typing import Any

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session

from src.models.base import Base


class TestModel(Base):
    """Test model for testing base model functionality."""

    __tablename__ = "test_model"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    value = Column(Integer)


@pytest.fixture
def test_model(db_session: Session) -> TestModel:
    """Create a test model instance."""
    model = TestModel(id=1, name="test", value=42)
    db_session.add(model)
    db_session.commit()
    return model


def test_tablename_generation():
    """Test automatic table name generation."""
    assert TestModel.__tablename__ == "test_model"


def test_created_at_default(test_model: TestModel):
    """Test created_at default value."""
    assert isinstance(test_model.created_at, datetime)
    assert test_model.created_at <= datetime.utcnow()


def test_updated_at_default(test_model: TestModel):
    """Test updated_at default value."""
    assert isinstance(test_model.updated_at, datetime)
    assert test_model.updated_at <= datetime.utcnow()


def test_repr(test_model: TestModel):
    """Test string representation."""
    repr_str = str(test_model)
    assert "TestModel" in repr_str
    assert "id=1" in repr_str
    assert "name='test'" in repr_str
    assert "value=42" in repr_str


def test_to_dict(test_model: TestModel):
    """Test conversion to dictionary."""
    model_dict = test_model.to_dict()
    assert isinstance(model_dict, dict)
    assert model_dict["id"] == 1
    assert model_dict["name"] == "test"
    assert model_dict["value"] == 42
    assert isinstance(model_dict["created_at"], str)
    assert isinstance(model_dict["updated_at"], str)


def test_model_update(db_session: Session, test_model: TestModel):
    """Test model update functionality."""
    old_updated_at = test_model.updated_at
    test_model.name = "updated"
    db_session.commit()
    assert test_model.updated_at > old_updated_at
