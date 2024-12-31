import pandas as pd
from typing import Dict, List, Optional, Union
from datetime import datetime
import re
import os


class NBAGameDataTransformer:
    """Transform and clean NBA game data from web scraping"""

    def __init__(self):
        """Initialize the transformer"""
        self.required_columns = [
            "Date",
            "Start (ET)",
            "Visitor/Neutral",
            "PTS",
            "Home/Neutral",
            "PTS.1",  # Second PTS column
            "",  # Empty column for OT
        ]

    def _extract_team_name(self, team_str: str) -> str:
        """Extract clean team name from HTML string"""
        # Extract team name from format like "[Boston Celtics](/teams/BOS/2012.html)"
        match = re.search(r"\[(.*?)\]", team_str)
        return match.group(1) if match else team_str

    def _extract_team_code(self, team_str: str) -> str:
        """Extract team code from HTML string"""
        # Extract team code from format like "[Boston Celtics](/teams/BOS/2012.html)"
        match = re.search(r"/teams/(\w+)/", team_str)
        return match.group(1) if match else None

    def _parse_date(self, date_str: str) -> str:
        """Convert date string to ISO format with UTC indicator"""
        # Extract date from format like "[Sun, Dec 25, 2011](/boxscores/index.fcgi?month=12&day=25&year=2011)"
        match = re.search(r"month=(\d+)&day=(\d+)&year=(\d+)", date_str)
        if match:
            month, day, year = match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return f"{date_obj.isoformat()}Z"  # Add Z to indicate UTC
            except ValueError:
                return None
        return None

    def _standardize_time(self, time_str: str) -> str:
        """
        Convert 12-hour time format to standardized format
        Example: '12:00p' -> '12:00 PM', '7:30p' -> '7:30 PM'
        """
        if not time_str:
            return None

        # Extract hours, minutes, and period
        match = re.match(r"(\d+):(\d+)([ap])", time_str)
        if not match:
            return time_str

        hours, minutes, period = match.groups()
        period = "PM" if period == "p" else "AM"

        # Ensure consistent formatting
        return f"{hours}:{minutes} {period}"

    def _parse_overtime(self, ot_str: str) -> Optional[int]:
        """Parse overtime period count"""
        if not ot_str:
            return 0
        match = re.match(r"(\d+)?OT", ot_str)
        if match:
            # If there's a number before OT, use it, otherwise it's 1 OT
            return int(match.group(1)) if match.group(1) else 1
        return 0

    def transform_raw_data(self, data: List[Dict]) -> pd.DataFrame:
        """
        Transform raw scraped data into clean DataFrame

        Args:
            data: List of dictionaries containing raw game data

        Returns:
            DataFrame with cleaned and normalized data
        """
        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Rename duplicate PTS column
        if "PTS" in df.columns and "PTS.1" not in df.columns:
            df.columns = pd.Series(df.columns).replace({"PTS": ["PTS", "PTS.1"]})

        # Verify required columns
        missing_cols = set(self.required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        # Clean and transform data
        transformed_data = {
            "game_date": df["Date"].apply(self._parse_date),
            "start_time": df["Start (ET)"].apply(self._standardize_time),
            "visitor_team": df["Visitor/Neutral"].apply(self._extract_team_name),
            "visitor_team_code": df["Visitor/Neutral"].apply(self._extract_team_code),
            "visitor_team_points": pd.to_numeric(df["PTS"], errors="coerce"),
            "home_team": df["Home/Neutral"].apply(self._extract_team_name),
            "home_team_code": df["Home/Neutral"].apply(self._extract_team_code),
            "home_team_points": pd.to_numeric(df["PTS.1"], errors="coerce"),
            "overtime_periods": df[""].apply(self._parse_overtime),
        }

        # Create new DataFrame with transformed data
        clean_df = pd.DataFrame(transformed_data)

        # Add derived columns
        clean_df["season_year"] = clean_df["game_date"].apply(
            lambda x: int(x[:4]) if pd.notnull(x) else None
        )

        # Convert points columns to integers
        clean_df["visitor_team_points"] = clean_df["visitor_team_points"].astype(
            "Int64"
        )
        clean_df["home_team_points"] = clean_df["home_team_points"].astype("Int64")

        # Add game outcome columns (binary)
        clean_df["home_team_won"] = (
            clean_df["home_team_points"] > clean_df["visitor_team_points"]
        ).astype(int)
        clean_df["visitor_team_won"] = (
            clean_df["visitor_team_points"] > clean_df["home_team_points"]
        ).astype(int)
        clean_df["point_difference"] = abs(
            clean_df["home_team_points"] - clean_df["visitor_team_points"]
        )

        # Add ML-friendly features
        clean_df["is_overtime"] = (clean_df["overtime_periods"] > 0).astype(int)

        # Ensure all text columns are strings
        text_columns = [
            "visitor_team",
            "visitor_team_code",
            "home_team",
            "home_team_code",
            "start_time",
        ]
        for col in text_columns:
            clean_df[col] = clean_df[col].astype(str)

        return clean_df

    def validate_transformed_data(self, df: pd.DataFrame) -> bool:
        """
        Validate transformed data meets requirements

        Args:
            df: Transformed DataFrame to validate

        Returns:
            bool indicating if data is valid
        """
        try:
            # Check for required columns
            required_transformed_columns = {
                "game_date",
                "start_time",
                "visitor_team",
                "visitor_team_code",
                "visitor_team_points",
                "home_team",
                "home_team_code",
                "home_team_points",
                "overtime_periods",
                "season_year",
                "home_team_won",
                "visitor_team_won",
                "point_difference",
                "is_overtime",
            }

            missing_cols = required_transformed_columns - set(df.columns)
            if missing_cols:
                print(f"Missing columns: {missing_cols}")
                return False

            # Check for null values in critical columns
            critical_columns = [
                "game_date",
                "visitor_team_code",
                "home_team_code",
                "visitor_team_points",
                "home_team_points",
                "home_team_won",
                "visitor_team_won",
            ]

            null_counts = df[critical_columns].isnull().sum()
            if null_counts.any():
                print(
                    f"Null values found in critical columns:\n{null_counts[null_counts > 0]}"
                )
                return False

            # Validate points ranges
            if (df["visitor_team_points"] < 0).any() or (
                df["home_team_points"] < 0
            ).any():
                print("Invalid negative points found")
                return False

            # Validate overtime periods
            if (df["overtime_periods"] < 0).any():
                print("Invalid negative overtime periods found")
                return False

            # Validate binary columns
            binary_columns = ["home_team_won", "visitor_team_won", "is_overtime"]
            for col in binary_columns:
                if not df[col].isin([0, 1]).all():
                    print(f"Invalid values in binary column {col}")
                    return False

            # Validate game outcomes
            if (df["home_team_won"] + df["visitor_team_won"] != 1).any():
                print("Invalid game outcomes: each game must have exactly one winner")
                return False

            # Validate time format
            time_pattern = re.compile(r"\d{1,2}:\d{2} [AP]M")
            invalid_times = ~df["start_time"].str.match(time_pattern)
            if invalid_times.any():
                print("Invalid time format found")
                print(df.loc[invalid_times, "start_time"])
                return False

            return True

        except Exception as e:
            print(f"Validation error: {e}")
            return False

    def get_database_ready_dict(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert DataFrame to a list of dictionaries ready for database insertion

        Args:
            df: Transformed DataFrame

        Returns:
            List of dictionaries matching database schema
        """
        return df.to_dict(orient="records")


# Example usage:
def main():
    # Sample data
    sample_data = [
        {
            "Date": "[Sun, Dec 25, 2011](/boxscores/index.fcgi?month=12&day=25&year=2011)",
            "Start (ET)": "12:00p",
            "Visitor/Neutral": "[Boston Celtics](/teams/BOS/2012.html)",
            "PTS": 104,
            "Home/Neutral": "[New York Knicks](/teams/NYK/2012.html)",
            "PTS": 106,
            "": "",
            "Attend.": "19,763",
            "LOG": "2:47",
            "Arena": "Madison Square Garden (IV)",
            "Notes": "",
        }
    ]

    # Transform data
    transformer = NBAGameDataTransformer()
    transformed_df = transformer.transform_raw_data(sample_data)

    # Validate transformation
    is_valid = transformer.validate_transformed_data(transformed_df)
    print(f"\nData validation: {'Passed' if is_valid else 'Failed'}")

    if is_valid:
        # Display sample of transformed data
        print("\nSample of transformed data:")
        print(transformed_df.head())

        # Display data types
        print("\nData types:")
        print(transformed_df.dtypes)

        # Display summary statistics
        print("\nSummary statistics:")
        print(transformed_df.describe(include="all"))


if __name__ == "__main__":
    main()
