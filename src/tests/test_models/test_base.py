import pytest
from datetime import datetime
from sqlalchemy import Column, Integer, String
from src.models.base import BaseModel


class TestModel(BaseModel):
    """Test model for BaseModel testing."""

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(Integer)


def test_tablename_generation():
    """Test automatic table name generation."""
    assert TestModel.__tablename__ == "testmodel"


def test_created_at_default():
    """Test created_at field default value."""
    model = TestModel(name="test", value=42)
    assert isinstance(model.created_at, datetime)
    assert isinstance(model.updated_at, datetime)


def test_repr():
    """Test string representation of model."""
    model = TestModel(name="test", value=42)
    repr_str = repr(model)
    assert "TestModel" in repr_str
    assert "name='test'" in repr_str
    assert "value=42" in repr_str


def test_to_dict():
    """Test conversion of model to dictionary."""
    model = TestModel(name="test", value=42)
    model_dict = model.to_dict()

    assert isinstance(model_dict, dict)
    assert model_dict["name"] == "test"
    assert model_dict["value"] == 42
    assert "created_at" in model_dict
    assert "updated_at" in model_dict
