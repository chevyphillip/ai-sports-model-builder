# Data Collection Documentation

## Overview
This document describes the data collection process, including sources, methods, and data transformation.

## Data Sources

### The Odds API
Primary source for sports betting data:
- Sports information
- Odds from various bookmakers
- Game scores and results
- Upcoming events

Example usage:
```python
from src.api.odds_api import OddsAPI

client = OddsAPI(api_key="your_api_key")
sports = client.get_sports()
odds = client.get_odds("basketball_nba")
scores = client.get_scores("basketball_nba")
```

## Data Collection Process

### 1. Initial Data Collection
- Get list of available sports
- Filter relevant sports
- Get odds for each sport
- Get scores for each sport
- Store raw data

### 2. Data Transformation
- Clean and validate data
- Normalize team names
- Convert odds formats
- Handle missing data
- Aggregate multiple sources

### 3. Data Storage
- Store in database
- Update existing records
- Handle duplicates
- Maintain history

## Data Models

### Raw Data
```python
class RawData(Base):
    __tablename__ = "raw_data"
    id = Column(Integer, primary_key=True)
    source = Column(String(50), nullable=False)
    data_type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow)
```

### Transformed Data
```python
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True)
    sport = Column(String(50), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False)
    odds = Column(JSON)
    scores = Column(JSON)
```

## Error Handling

### API Errors
- Rate limiting
- Connection issues
- Invalid responses
- Timeout handling

### Data Validation
- Required fields
- Data types
- Value ranges
- Relationships

### Recovery
- Retry logic
- Partial updates
- Error logging
- Notifications

## Scheduling

### Collection Schedule
- Sports data: Every 6 hours
- Odds data: Every 15 minutes
- Scores data: Every 5 minutes

### Job Management
```python
@scheduled_job("cron", hour="*/6")
def collect_sports_data():
    """Collect sports data every 6 hours."""
    client = OddsAPI()
    sports = client.get_sports()
    store_sports_data(sports)
```

## Data Quality

### Validation Rules
1. Required fields must be present
2. Dates must be valid
3. Teams must exist
4. Odds must be positive
5. Scores must be non-negative

### Monitoring
- Data completeness
- Data accuracy
- Collection timing
- Error rates
- API usage

## Testing

### Unit Tests
```python
def test_data_transformation(raw_data):
    transformed = transform_data(raw_data)
    assert transformed.home_team is not None
    assert transformed.away_team is not None
    assert transformed.start_time is not None
```

### Integration Tests
```python
def test_data_collection_flow():
    collect_and_store_data()
    assert DataModel.query.count() > 0
```

## Best Practices
1. Document data sources
2. Version raw data
3. Handle timezones
4. Validate early
5. Log extensively
6. Monitor API usage
7. Clean data properly
8. Handle edge cases
9. Test thoroughly
10. Document assumptions

## Future Improvements
1. Add more data sources
2. Improve validation
3. Enhance monitoring
4. Optimize scheduling
5. Add data versioning
6. Implement caching
7. Add data quality metrics
8. Improve error recovery
9. Add data lineage
10. Enhance documentation 