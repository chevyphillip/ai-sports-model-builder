"""Transform NBA schedule data into database format."""

from datetime import datetime
from typing import Dict, List
import pandas as pd


class NBAScheduleTransformer:
    """Transform NBA schedule data into database format."""

    def transform_games(self, data: Dict) -> pd.DataFrame:
        """Transform game data into a DataFrame suitable for database insertion.

        Args:
            data: Raw schedule data from collector

        Returns:
            DataFrame with transformed game data
        """
        if not data or "games" not in data:
            return pd.DataFrame()

        # Convert games list to DataFrame
        df = pd.DataFrame(data["games"])

        # Add metadata columns
        df["season_year"] = data["metadata"]["season_year"]
        df["season"] = data["metadata"]["season"]
        df["source"] = data["metadata"]["source"]
        df["scraped_at"] = pd.to_datetime(data["metadata"]["scraped_at"])

        # Convert date strings to datetime
        df["game_date"] = pd.to_datetime(df["date"])

        # Clean numeric fields
        df["visitor_points"] = pd.to_numeric(df["visitor_points"], errors="coerce")
        df["home_points"] = pd.to_numeric(df["home_points"], errors="coerce")
        df["attendance"] = (
            df["attendance"]
            .str.replace(",", "")  # Remove commas
            .pipe(pd.to_numeric, errors="coerce")  # Convert to numeric
        )

        # Generate unique game ID
        df["game_id"] = df.apply(
            lambda row: f"{row['game_date'].strftime('%Y%m%d')}_{row['visitor_team']}_{row['home_team']}".lower().replace(
                " ", "_"
            ),
            axis=1,
        )

        # Reorder columns
        columns = [
            "game_id",
            "game_date",
            "season_year",
            "season",
            "visitor_team",
            "visitor_points",
            "home_team",
            "home_points",
            "attendance",
            "arena",
            "box_score_url",
            "source",
            "scraped_at",
        ]
        df = df[columns]

        return df

    def transform_to_dict_records(self, data: Dict) -> List[Dict]:
        """Transform data into a list of dictionaries suitable for database insertion.

        Args:
            data: Raw schedule data from collector

        Returns:
            List of dictionaries with transformed game data
        """
        df = self.transform_games(data)
        if df.empty:
            return []

        # Convert DataFrame to list of dictionaries
        records = df.to_dict(orient="records")

        # Convert datetime objects to ISO format strings
        for record in records:
            record["game_date"] = record["game_date"].isoformat()
            record["scraped_at"] = record["scraped_at"].isoformat()

        return records
