"""Script to collect and load NBA schedule data."""

import asyncio
from typing import Optional
from .nba_schedule_collector import NBAScheduleCollector
from .nba_schedule_transformer import NBAScheduleTransformer
from .nba_schedule_loader import NBAScheduleLoader


async def collect_and_load_schedule(
    season_year: int,
    month: Optional[str] = None,
    save_raw: bool = True,
) -> int:
    """Collect and load NBA schedule data.

    Args:
        season_year: The year of the season (e.g., 2012 for 2011-12 season)
        month: Optional month name in lowercase (e.g., 'december', 'january')
        save_raw: Whether to save the raw data to file

    Returns:
        Number of games loaded into the database
    """
    # Initialize components
    collector = NBAScheduleCollector()
    transformer = NBAScheduleTransformer()
    loader = NBAScheduleLoader()

    # Collect data
    if month:
        data = await collector.collect_month(season_year, month, save_raw)
    else:
        data = await collector.collect_season(season_year, save_raw)

    if not data:
        return 0

    # Transform data
    records = transformer.transform_to_dict_records(data)
    if not records:
        return 0

    # Load data
    num_loaded = loader.load_games(records)
    return num_loaded


async def main():
    """Main entry point for collecting NBA schedule data."""
    # Example: Collect and load 2011-12 season data
    season_year = 2012
    num_loaded = await collect_and_load_schedule(season_year)
    print(
        f"Finished loading {num_loaded} games for {season_year-1}-{str(season_year)[2:]} season"
    )


if __name__ == "__main__":
    asyncio.run(main())
