"""Script to collect NBA schedule data using FireCrawl."""

import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from .firecrawl_client import FireCrawlClient


class NBAScheduleCollector:
    """Collector for NBA schedule data."""

    def __init__(
        self, api_key: Optional[str] = None, output_dir: str = "data/raw/nba_schedules"
    ):
        """Initialize the collector.

        Args:
            api_key: Optional FireCrawl API key
            output_dir: Directory to save raw data
        """
        self.client = FireCrawlClient(api_key=api_key)
        self.output_dir = output_dir

    async def collect_season(self, season_year: int, save_raw: bool = True) -> Dict:
        """Collect schedule data for a full season.

        Args:
            season_year: The year of the season (e.g., 2012 for 2011-12 season)
            save_raw: Whether to save the raw data to file

        Returns:
            Dictionary containing the scraped schedule data
        """
        print(
            f"Collecting schedule data for {season_year-1}-{str(season_year)[2:]} season..."
        )

        # Scrape the schedule data
        data = await self.client.scrape_nba_schedule(season_year)

        if not data:
            print(f"No data found for season {season_year}")
            return {}

        # Save raw data if requested
        if save_raw:
            filepath = self.client.save_schedule_data(
                data, season_year, self.output_dir
            )
            print(f"Saved raw data to: {filepath}")

        return data

    async def collect_month(
        self, season_year: int, month: str, save_raw: bool = True
    ) -> Dict:
        """Collect schedule data for a specific month.

        Args:
            season_year: The year of the season (e.g., 2012 for 2011-12 season)
            month: Month name in lowercase (e.g., 'december', 'january')
            save_raw: Whether to save the raw data to file

        Returns:
            Dictionary containing the scraped schedule data
        """
        print(f"Collecting schedule data for {month} {season_year}...")

        # Scrape the schedule data
        data = await self.client.scrape_nba_schedule(season_year, month)

        if not data:
            print(f"No data found for {month} {season_year}")
            return {}

        # Save raw data if requested
        if save_raw:
            filepath = self.client.save_schedule_data(
                data, season_year, self.output_dir
            )
            print(f"Saved raw data to: {filepath}")

        return data


async def main():
    """Main entry point for collecting NBA schedule data."""
    # Initialize collector with API key from environment
    collector = NBAScheduleCollector()

    # Example: Collect 2011-12 season data
    data = await collector.collect_season(2012)
    print(f"Collected {len(data.get('games', []))} games")


if __name__ == "__main__":
    asyncio.run(main())
