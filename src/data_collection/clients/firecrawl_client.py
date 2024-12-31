"""FireCrawl API client for scraping NBA schedule data."""

import os
from typing import Dict, Optional, List
from datetime import datetime, timezone
import json
import requests
from bs4 import BeautifulSoup
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import quote_plus


class FireCrawlClient:
    """Client for interacting with the FireCrawl API to scrape NBA schedule data."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the FireCrawl client.

        Args:
            api_key: Optional API key for FireCrawl. If not provided, will try to get from environment.
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FireCrawl API key not provided and not found in environment"
            )

        self.base_url = "https://api.firecrawl.io/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Set up database connection
        self.db_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "sslmode": "require",
        }

    def get_db_connection(self):
        """Get a database connection."""
        return psycopg2.connect(**self.db_params)

    def scrape_url(self, url: str, params: Dict = None) -> Dict:
        """Make a request to the FireCrawl API.

        Args:
            url: URL to scrape
            params: Optional parameters for the scrape request

        Returns:
            Dictionary containing the scraped data
        """
        endpoint = f"{self.base_url}/scrape"
        data = {
            "url": url,
            "formats": ["html"],
            "onlyMainContent": True,
            "waitFor": 5000,
            **(params or {}),
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error making request to FireCrawl API: {e}")
            return {}

    def insert_game(self, game_data: Dict) -> None:
        """Insert or update a game in the database.

        Args:
            game_data: Dictionary containing game data
        """
        upsert_query = """
            INSERT INTO nba_game_lines.games (
                game_id, game_date, season_year, season,
                visitor_team, visitor_points, home_team, home_points,
                arena, source, scraped_at
            ) VALUES (
                %(game_id)s, %(game_date)s, %(season_year)s, %(season)s,
                %(visitor_team)s, %(visitor_points)s, %(home_team)s, %(home_points)s,
                %(arena)s, %(source)s, %(scraped_at)s
            )
            ON CONFLICT (game_id) DO UPDATE SET
                visitor_points = EXCLUDED.visitor_points,
                home_points = EXCLUDED.home_points,
                updated_at = CURRENT_TIMESTAMP,
                scraped_at = EXCLUDED.scraped_at
        """

        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(upsert_query, game_data)
            conn.commit()

    def generate_nba_schedule_url(self, season_year: int, month: str = None) -> str:
        """Generate URL for NBA schedule page.

        Args:
            season_year: The year of the season (e.g., 2012 for 2011-12 season)
            month: Optional month name in lowercase (e.g., 'december', 'january')

        Returns:
            URL for the NBA schedule page
        """
        base_url = (
            f"https://www.basketball-reference.com/leagues/NBA_{season_year}_games"
        )
        if month:
            month = month.lower()
            return f"{base_url}-{month}.html"
        return f"{base_url}.html"

    def scrape_nba_schedule(
        self,
        season_year: int,
        month: str = None,
    ) -> List[Dict]:
        """Scrape NBA schedule data for a specific season and month.

        Args:
            season_year: The year of the season (e.g., 2024 for 2023-24 season)
            month: Optional month name in lowercase (e.g., 'december', 'january')

        Returns:
            List of dictionaries containing the scraped schedule data
        """
        url = self.generate_nba_schedule_url(season_year, month)

        try:
            # Use the FireCrawl API to scrape the URL
            response = self.scrape_url(url)

            if not response or not response.get("html"):
                logging.warning(f"No HTML content found in response: {response}")
                return []

            # Process the response data
            return self._process_schedule_data(response, season_year, month)
        except Exception as e:
            logging.error(f"Error scraping NBA schedule: {e}")
            return []

    def _process_schedule_data(
        self, raw_data: Dict, season_year: int, month: str = None
    ) -> List[Dict]:
        """Process scraped schedule data.

        Args:
            raw_data: Raw data from FireCrawl API
            season_year: The year of the season (e.g., 2024 for 2024-25 season)
            month: Optional month name

        Returns:
            List of dictionaries containing processed schedule data
        """
        processed_data = []

        if not raw_data or not raw_data.get("html"):
            return processed_data

        # Extract game rows from HTML table
        html_content = raw_data["html"]
        soup = BeautifulSoup(html_content, "html.parser")
        schedule_table = soup.find("table", id="schedule")
        if not schedule_table:
            logging.warning("No schedule table found in HTML")
            return processed_data

        game_rows = schedule_table.select("tbody tr")
        if not game_rows:
            logging.warning("No game rows found in schedule table")
            return processed_data

        for row in game_rows:
            try:
                # Extract date
                date_cell = row.select_one("th[data-stat='date_game'] a")
                if not date_cell:
                    continue
                date_str = date_cell.text.strip()
                try:
                    date = datetime.strptime(date_str, "%a, %b %d, %Y")
                except ValueError as e:
                    logging.error(f"Error parsing date {date_str}: {e}")
                    continue

                # Extract visitor team and points
                visitor_team = row.select_one("td[data-stat='visitor_team_name']")
                visitor_points = row.select_one("td[data-stat='visitor_pts']")
                if not visitor_team or not visitor_points:
                    continue

                # Extract home team and points
                home_team = row.select_one("td[data-stat='home_team_name']")
                home_points = row.select_one("td[data-stat='home_pts']")
                if not home_team or not home_points:
                    continue

                # Extract arena
                arena = row.select_one("td[data-stat='arena_name']")
                if not arena:
                    continue

                # Clean team names and create abbreviations
                home_team_name = home_team.text.strip()
                visitor_team_name = visitor_team.text.strip()
                home_abbr = "".join(c for c in home_team_name.upper() if c.isalpha())[
                    :3
                ]
                visitor_abbr = "".join(
                    c for c in visitor_team_name.upper() if c.isalpha()
                )[:3]

                # Generate new format game_id: NBA-YYYY-MM-DD-HOME-AWAY
                game_id = f"NBA-{date.strftime('%Y-%m-%d')}-{home_abbr}-{visitor_abbr}"

                # Determine season year and season string
                actual_season_year = (
                    season_year + 1 if date.month >= 10 else season_year
                )
                season = f"{actual_season_year-1}-{str(actual_season_year)[2:]}"

                game = {
                    "game_id": game_id,
                    "game_date": date.date(),  # Store date without time
                    "season_year": actual_season_year,
                    "season": season,
                    "visitor_team": visitor_team_name,
                    "visitor_points": int(visitor_points.text.strip() or 0),
                    "home_team": home_team_name,
                    "home_points": int(home_points.text.strip() or 0),
                    "arena": arena.text.strip(),
                    "source": "basketball-reference",
                    "scraped_at": datetime.now(timezone.utc),
                }
                processed_data.append(game)
            except (AttributeError, ValueError) as e:
                logging.error(f"Error processing game row: {e}")
                continue

        return processed_data

    def _parse_attendance(self, attendance_str: str) -> Optional[int]:
        """Parse attendance string to integer.

        Args:
            attendance_str: Attendance string (e.g., "19,763")

        Returns:
            Attendance as integer or None if invalid
        """
        try:
            return int(attendance_str.replace(",", ""))
        except (ValueError, AttributeError):
            return None

    def save_schedule_data(self, data: Dict, season_year: int, output_dir: str) -> str:
        """Save schedule data to a JSON file.

        Args:
            data: Schedule data to save
            season_year: Season year for filename
            output_dir: Directory to save the file in

        Returns:
            Path to the saved file
        """
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"nba_schedule_{season_year}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Save data to file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath
