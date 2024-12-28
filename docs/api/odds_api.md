# Odds API Client Documentation

## Overview
The Odds API client provides a Python interface to The Odds API service, allowing access to sports betting data, odds, and scores.

## Installation
The client requires the following dependencies:
- `requests`
- `logging`

## Configuration
The client requires an API key from The Odds API. You can obtain one by signing up at [The Odds API](https://the-odds-api.com/).

## Usage

### Initialization
```python
from src.api.odds_api import OddsAPI

client = OddsAPI(api_key="your_api_key")
```

### Available Methods

#### Get Sports List
```python
sports = client.get_sports()
```
Returns a list of available sports with their metadata.

#### Get Odds
```python
odds = client.get_odds(sport="basketball_nba")
```
Returns odds data for a specific sport.

#### Get Scores
```python
scores = client.get_scores(sport="basketball_nba", days_from=1)
```
Returns scores data for a specific sport.

#### Get Events
```python
events = client.get_events(sport="basketball_nba")
```
Returns upcoming events for a specific sport.

#### Get Event Odds
```python
event_odds = client.get_event_odds(
    sport="basketball_nba",
    event_id="1",
    regions="us",
    markets="h2h,spreads,totals",
    date_format="iso",
    odds_format="decimal"
)
```
Returns odds data for a specific event.

## Response Formats

### Sports Response
```json
[
    {
        "key": "basketball_nba",
        "group": "Basketball",
        "title": "NBA",
        "description": "US Basketball",
        "active": true,
        "has_outrights": false
    }
]
```

### Odds Response
```json
[
    {
        "id": "1",
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2024-01-01T00:00:00Z",
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "bookmakers": [
            {
                "key": "fanduel",
                "title": "FanDuel",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Los Angeles Lakers", "price": 1.91},
                            {"name": "Golden State Warriors", "price": 1.91}
                        ]
                    }
                ]
            }
        ]
    }
]
```

### Scores Response
```json
[
    {
        "id": "1",
        "sport_key": "basketball_nba",
        "sport_title": "NBA",
        "commence_time": "2024-01-01T00:00:00Z",
        "completed": true,
        "home_team": "Los Angeles Lakers",
        "away_team": "Golden State Warriors",
        "scores": [
            {"name": "Los Angeles Lakers", "score": 120},
            {"name": "Golden State Warriors", "score": 110}
        ],
        "last_update": "2024-01-01T02:30:00Z"
    }
]
```

## Error Handling
The client handles various error cases:
- 404: Resource not found
- 401: Unauthorized (invalid API key)
- 429: Rate limit exceeded
- 500: Server error

All errors are logged using the Python logging module, and the client returns an empty list in case of any error.

## Rate Limiting
The Odds API has rate limits based on your subscription plan. The client does not implement rate limiting internally, so you should handle this in your application logic.

## Best Practices
1. Store your API key securely (e.g., in environment variables)
2. Implement proper error handling in your application
3. Cache responses when appropriate to avoid hitting rate limits
4. Use appropriate market types based on your needs
5. Handle timezone differences in timestamps

## Testing
The client comes with comprehensive tests covering:
- Basic functionality
- Error handling
- Parameter validation
- Edge cases

Run tests using pytest:
```bash
python -m pytest tests/integration/test_odds_api.py -v
``` 