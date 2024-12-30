# GET historical odds

Returns a snapshot of games with bookmaker odds for a given sport, region and market, at a given historical timestamp. Historical odds data is available from June 6th 2020, with snapshots taken at 10 minute intervals. From September 2022, historical odds snapshots are available at 5 minute intervals. This endpoint is only available on paid usage plans.

## Endpoint

```
GET /v4/historical/sports/{sport}/odds?apiKey={apiKey}®ions={regions}&markets={markets}&date={date}
```

## Parameters

Parameters are the same as for the /odds endpoint, with the addition of the date parameter.

date The timestamp of the data snapshot to be returned, specified in ISO8601 format, for example ```2021-10-18T12:00:00Z``` The historical odds API will return the closest snapshot equal to or earlier than the provided date parameter

## Example Request

```
GET https://api.the-odds-api.com/v4/historical/sports/americanfootball\_nfl/odds/?apiKey={API_KEY}®ions=us&markets=h2h&oddsFormat=american&date=2021-10-18T12:00:00Z
```

## Example Response

The response schema is the same as that of the /odds endpoint, but wrapped in a structure that contains information about the snapshot, including:

```timestamp:``` The timestamp of the snapshot. This will be the closest available timestamp equal to or earlier than the provided date parameter.

```previous_timestamp:``` the preceding available timestamp. This can be used as the date parameter in a new request to move back in time.

```next_timestamp```: The next available timestamp. This can be used as the date parameter in a new request to move forward in time.


```json
{
    "timestamp": "2021-10-18T11:55:00Z",
    "previous_timestamp": "2021-10-18T11:45:00Z",
    "next_timestamp": "2021-10-18T12:05:00Z",
    "data": [
        {
            "id": "4edd5ce090a3ec6192053b10d27b87b0",
            "sport_key": "americanfootball_nfl",
            "sport_title": "NFL",
            "commence_time": "2021-10-19T00:15:00Z",
            "home_team": "Tennessee Titans",
            "away_team": "Buffalo Bills",
            "bookmakers": [
                {
                    "key": "draftkings",
                    "title": "DraftKings",
                    "last_update": "2021-10-18T11:48:09Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {
                                    "name": "Buffalo Bills",
                                    "price": -294
                                },
                                {
                                    "name": "Tennessee Titans",
                                    "price": 230
                                }
                            ]
                        }
                    ]
                },
                {
                    "key": "twinspires",
                    "title": "TwinSpires",
                    "last_update": "2021-10-18T11:48:00Z",
                    "markets": [
                        {
                            "key": "h2h",
                            "outcomes": [
                                {
                                    "name": "Buffalo Bills",
                                    "price": -278
                                },
                                {
                                    "name": "Tennessee Titans",
                                    "price": 220
                                }
                            ]
                        }
                    ]
                }
```