"""Script to test NBA schedule scraping."""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(os.path.join(project_root, ".env"))

from src.data_collection.firecrawl_client import FireCrawlClient


def test_scrape():
    """Test NBA schedule scraping."""
    # Initialize client
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("Error: FIRECRAWL_API_KEY not found in environment!")
        return

    client = FireCrawlClient(api_key=api_key)

    # Get current season year
    current_year = datetime.now().year

    print(
        f"\nScraping NBA schedule for {current_year-1}-{str(current_year)[2:]} season..."
    )

    # Scrape the schedule
    result = client.scrape_nba_schedule(
        season_year=current_year,
        use_local=False,  # Use live scraping
    )

    # Check if we got any data
    if not result or not result.get("games"):
        print("No data found!")
        return

    # Print metadata
    print("\nMetadata:")
    for key, value in result["metadata"].items():
        print(f"{key}: {value}")

    # Print games
    print(f"\nFound {len(result['games'])} games:")
    for i, game in enumerate(result["games"][:5], 1):  # Show first 5 games
        print(f"\nGame {i}:")
        print(f"Date: {game['date']}")
        print(f"Teams: {game['visitor_team']} @ {game['home_team']}")
        print(f"Score: {game['visitor_points']} - {game['home_points']}")
        print(f"Venue: {game['arena']}")
        print(f"Attendance: {game['attendance']}")
        print(f"Box Score: {game['box_score_url']}")

    if len(result["games"]) > 5:
        print(f"\n... and {len(result['games']) - 5} more games")

    # Save the raw data for inspection
    output_file = "data/raw/nba_schedules/latest_scrape.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nFull data saved to: {output_file}")


if __name__ == "__main__":
    test_scrape()
