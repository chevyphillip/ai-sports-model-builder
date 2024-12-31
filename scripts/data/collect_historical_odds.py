"""Script to collect historical odds data for NBA games."""

from datetime import datetime, timezone
import argparse
from src.services.historical_data_service import HistoricalDataService


def main():
    """Run the historical odds data collection."""
    parser = argparse.ArgumentParser(
        description="Collect historical odds data for NBA games"
    )
    parser.add_argument(
        "--start-date", type=str, required=True, help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date", type=str, required=True, help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Time interval between odds snapshots in minutes (default: 5)",
    )

    args = parser.parse_args()

    # Parse dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )
    except ValueError as e:
        print(f"Error parsing dates: {e}")
        return

    if end_date < start_date:
        print("End date must be after start date")
        return

    # Initialize service
    service = HistoricalDataService()

    # Run collection
    try:
        print(f"Starting historical odds collection from {start_date} to {end_date}")
        print(f"Using {args.interval} minute intervals")

        service.collect_historical_odds(
            start_date=start_date, end_date=end_date, interval_minutes=args.interval
        )

        print("✅ Historical odds collection completed")

    except Exception as e:
        print(f"❌ Error during collection: {e}")


if __name__ == "__main__":
    main()
