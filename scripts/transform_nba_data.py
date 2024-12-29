"""Script to transform raw NBA schedule data into analysis-ready format."""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""

    def default(self, obj):
        if isinstance(obj, (datetime, pd.Timestamp)):
            return obj.isoformat()
        elif isinstance(obj, pd.Series):
            return obj.to_list()
        return super().default(obj)


def transform_nba_data(input_file: str = "data/raw/nba_schedules/latest_scrape.json"):
    """Transform raw NBA schedule data into analysis-ready format.

    Args:
        input_file: Path to raw JSON data file
    """
    # Load raw data
    with open(input_file, "r") as f:
        raw_data = json.load(f)

    # Convert to DataFrame
    df = pd.DataFrame(raw_data["games"])

    # Convert date strings to datetime
    df["date"] = pd.to_datetime(df["date"])

    # Extract additional date components
    df["season"] = raw_data["metadata"]["season"]
    df["season_year"] = raw_data["metadata"]["season_year"]
    df["game_day"] = df["date"].dt.strftime("%Y-%m-%d")  # Convert to string
    df["game_month"] = df["date"].dt.month
    df["game_year"] = df["date"].dt.year
    df["day_of_week"] = df["date"].dt.day_name()

    # Convert time to 24-hour format
    df["start_time_24h"] = pd.to_datetime(
        df["start_time"].str.replace("p", "PM").str.replace("a", "AM")
    ).dt.strftime("%H:%M")

    # Calculate game metrics
    df["total_score"] = df["visitor_points"] + df["home_points"]
    df["score_difference"] = abs(df["visitor_points"] - df["home_points"])
    df["home_win"] = df["home_points"] > df["visitor_points"]

    # Add overtime information
    # In NBA, regulation time is 48 minutes (4 quarters x 12 minutes)
    # Each overtime period is 5 minutes
    # Average points per minute in NBA is around 2.2-2.5
    # So each OT period typically adds ~11-13 points to total score
    df["overtime"] = False  # Default to no overtime

    # Criteria for overtime:
    # 1. Close game (within 3 possessions)
    # 2. Higher than average scoring
    # 3. Score pattern suggests extra period
    overtime_mask = (df["score_difference"] <= 9) & (  # Within 3 possessions
        # Either very high scoring close game
        ((df["total_score"] > 235) & (df["score_difference"] <= 6))
        |
        # Or moderately high scoring very close game
        ((df["total_score"] > 220) & (df["score_difference"] <= 3))
    )
    df.loc[overtime_mask, "overtime"] = True

    # Estimate number of overtime periods
    df["ot_periods"] = 0  # Default to 0
    df.loc[df["overtime"], "ot_periods"] = (
        ((df["total_score"] - 220) / 12)
        .clip(1, 4)  # Estimate based on extra scoring
        .round()  # Round to nearest whole number
        .astype(int)  # Convert to integer
    )

    # Clean attendance data
    df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce")

    # Create game_id using consistent format
    df["game_id"] = (
        df["date"].dt.strftime("%Y%m%d")
        + "_"
        + df["visitor_team"].str.replace(" ", "")
        + "_"
        + df["home_team"].str.replace(" ", "")
    )

    # Reorder columns for clarity
    columns = [
        "game_id",
        "season",
        "season_year",
        "date",
        "game_day",
        "game_month",
        "game_year",
        "day_of_week",
        "start_time_24h",
        "visitor_team",
        "home_team",
        "visitor_points",
        "home_points",
        "total_score",
        "score_difference",
        "home_win",
        "overtime",
        "ot_periods",
        "attendance",
        "arena",
    ]

    transformed_df = df[columns].copy()

    # Display sample and info
    print("\nTransformed Data Sample:")
    print(transformed_df.head(2).to_string())

    print("\nDataset Info:")
    print(transformed_df.info())

    print("\nSummary Statistics:")
    print(transformed_df.describe(include="all").to_string())

    # Convert DataFrame to dict with proper datetime handling
    games_data = json.loads(transformed_df.to_json(orient="records", date_format="iso"))

    # Save transformed data
    output_file = input_file.replace("latest_scrape.json", "transformed_data.json")
    transformed_data = {
        "games": games_data,
        "metadata": {
            "transformed_at": datetime.utcnow().isoformat(),
            "original_metadata": raw_data["metadata"],
            "total_games": len(transformed_df),
            "date_range": {
                "start": transformed_df["date"].min().strftime("%Y-%m-%d"),
                "end": transformed_df["date"].max().strftime("%Y-%m-%d"),
            },
            "summary_stats": {
                "avg_total_score": float(transformed_df["total_score"].mean()),
                "avg_attendance": float(transformed_df["attendance"].mean()),
                "home_win_pct": float(
                    (transformed_df["home_win"].sum() / len(transformed_df)) * 100
                ),
            },
        },
    }

    with open(output_file, "w") as f:
        json.dump(transformed_data, f, indent=2, cls=DateTimeEncoder)

    print(f"\nTransformed data saved to: {output_file}")
    return transformed_data


if __name__ == "__main__":
    transform_nba_data()
