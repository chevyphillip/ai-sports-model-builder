"""Basketball Reference scraper for NBA game data."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class BasketballReferenceScraper:
    """Scraper for basketball-reference.com."""

    BASE_URL = (
        "https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html"
    )
    MONTHS = [
        "october",
        "november",
        "december",
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
    ]

    def __init__(self):
        """Initialize the scraper."""
        self.session = requests.Session()
        # Add headers to mimic a browser
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )

    def _get_url(self, year: int, month: str) -> str:
        """Generate URL for a specific year and month."""
        return self.BASE_URL.format(year=year, month=month.lower())

    def _fetch_page(self, url: str) -> Optional[str]:
        """Fetch page content with error handling and rate limiting."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None

    def _parse_schedule_table(self, html: str) -> Optional[pd.DataFrame]:
        """Parse the schedule table from HTML content."""
        try:
            # Read all tables from the page
            dfs = pd.read_html(html, attrs={"id": "schedule"})
            if not dfs:
                logger.warning("No schedule table found")
                return None

            # Get the schedule table
            df = dfs[0]

            # Clean up the column names
            df.columns = [str(col) for col in df.columns]

            # Remove unwanted columns
            columns_to_drop = [
                col
                for col in df.columns
                if any(
                    x in str(col).upper()
                    for x in ["BOX SCORE", "NOTES", "ATTEND.", "LOG"]
                )
            ]
            df = df.drop(columns=columns_to_drop)

            # Handle the OT column (which might have an empty string as name)
            if "" in df.columns:
                df = df.rename(columns={"": "overtime"})

            # Clean up date column
            df["Date"] = pd.to_datetime(df["Date"])

            # Add metadata columns
            df["season_year"] = df["Date"].dt.year
            df["game_day"] = df["Date"].dt.day
            df["game_month"] = df["Date"].dt.month
            df["game_year"] = df["Date"].dt.year
            df["day_of_week"] = df["Date"].dt.strftime("%A")

            # Generate unique game IDs
            df["game_id"] = df.apply(
                lambda row: f"{row['Date'].strftime('%Y%m%d')}0{row['Home/Neutral'].split()[-1][:3].upper()}",
                axis=1,
            )

            return df
        except Exception as e:
            logger.error(f"Error parsing schedule table: {e}")
            return None

    def scrape_month(self, year: int, month: str) -> Optional[pd.DataFrame]:
        """Scrape game data for a specific month and year."""
        url = self._get_url(year, month)
        logger.info(f"Scraping {month} {year} from {url}")

        html = self._fetch_page(url)
        if not html:
            return None

        return self._parse_schedule_table(html)

    def scrape_season(self, year: int) -> List[pd.DataFrame]:
        """Scrape all available months for a specific season."""
        dfs = []
        for month in self.MONTHS:
            df = self.scrape_month(year, month)
            if df is not None and not df.empty:
                dfs.append(df)
        return dfs

    def scrape_multiple_seasons(
        self, start_year: int, end_year: int
    ) -> Dict[int, List[pd.DataFrame]]:
        """Scrape multiple seasons of data."""
        results = {}
        for year in range(start_year, end_year + 1):
            logger.info(f"Scraping season {year}")
            season_data = self.scrape_season(year)
            if season_data:
                results[year] = season_data
        return results
