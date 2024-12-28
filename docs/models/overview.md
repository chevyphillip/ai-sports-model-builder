# Database Models Documentation

## Overview
This document describes the database models used in the project. All models inherit from the `Base` class, which provides common functionality.

## Base Model
The `Base` class provides common functionality for all models:

```python
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
        """Convert model instance to dictionary."""
        result = {}
        for key in self.__mapper__.columns.keys():
            if not key.startswith("_"):
                value = getattr(self, key)
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[key] = value
        return result
```

### Common Fields
All models automatically include:
- `created_at`: Timestamp when the record was created
- `updated_at`: Timestamp when the record was last updated

### Common Methods
- `__repr__()`: String representation of the model
- `to_dict()`: Convert model to dictionary format

## Model Relationships
Models can be related using SQLAlchemy relationships:
- One-to-One
- One-to-Many
- Many-to-Many

Example:
```python
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    players = relationship("Player", back_populates="team")

class Player(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"))
    team = relationship("Team", back_populates="players")
```

## Data Types
Common column types:
- `Integer`: Whole numbers
- `String`: Text with optional length limit
- `DateTime`: Date and time values
- `Boolean`: True/False values
- `Float`: Decimal numbers
- `JSON`: JSON data
- `Enum`: Enumerated values

## Migrations
Database migrations are handled using Alembic:
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Apply migration: `alembic upgrade head`
3. Rollback migration: `alembic downgrade -1`

## Best Practices
1. Use meaningful table and column names
2. Define appropriate indexes
3. Set proper constraints
4. Handle relationships carefully
5. Use appropriate data types
6. Document model fields
7. Keep models focused
8. Use migrations for changes
9. Test model operations
10. Handle data validation

## Testing
Models are tested using pytest:
```python
def test_model_creation(db_session):
    model = MyModel(name="test")
    db_session.add(model)
    db_session.commit()
    assert model.id is not None
    assert model.created_at is not None
```

## Future Improvements
1. Add model validation
2. Implement soft delete
3. Add audit logging
4. Improve relationship handling
5. Add caching support 