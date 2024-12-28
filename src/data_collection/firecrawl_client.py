"""FireCrawl API client for scraping NBA schedule data."""

import os
from typing import Dict, Optional
from datetime import datetime
import json
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp


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

        self.app = FirecrawlApp(api_key=self.api_key)

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
        use_local: bool = True,
    ) -> Dict:
        """Scrape NBA schedule data for a specific season and month.

        Args:
            season_year: The year of the season (e.g., 2012 for 2011-12 season)
            month: Optional month name in lowercase (e.g., 'december', 'january')
            use_local: Whether to use local JSON file instead of making API call

        Returns:
            Dictionary containing the scraped schedule data
        """
        if use_local:
            return self._load_local_data(season_year, month)

        url = self.generate_nba_schedule_url(season_year, month)

        try:
            # Use the FireCrawl SDK to scrape the URL
            response = self.app.scrape_url(
                url,
                params={
                    "formats": ["html"],  # We only need HTML for parsing
                    "onlyMainContent": True,  # Focus on the main content (schedule table)
                    "waitFor": 5000,  # Wait 5 seconds for JavaScript content
                },
            )

            if not response or not response.get("html"):
                print(f"No HTML content found in response: {response}")
                return {}

            # Process the response data
            return self._process_schedule_data(
                {"html": response["html"]}, season_year, month
            )
        except Exception as e:
            print(f"Error scraping NBA schedule: {e}")
            return {}

    def _load_local_data(self, season_year: int, month: str = None) -> Dict:
        """Load schedule data from local JSON file.

        Args:
            season_year: The year of the season
            month: Optional month name

        Returns:
            Dictionary containing the schedule data
        """
        try:
            with open("firecrawle-data/results_01.json", "r") as f:
                raw_data = json.load(f)
                return self._process_schedule_data(raw_data, season_year, month)
        except Exception as e:
            print(f"Error loading local data: {e}")
            return {}

    def _process_schedule_data(
        self, raw_data: Dict, season_year: int, month: str = None
    ) -> Dict:
        """Process scraped schedule data.

        Args:
            raw_data: Raw data from FireCrawl API
            season_year: The year of the season
            month: Optional month name

        Returns:
            Dictionary containing processed schedule data
        """
        processed_data = {
            "games": [],
            "metadata": {
                "scraped_at": datetime.utcnow().isoformat(),
                "season_year": season_year,
                "season": f"{season_year-1}-{str(season_year)[2:]}",
                "month": month,
            },
        }

        if not raw_data or not raw_data.get("html"):
            return processed_data

        # Extract game rows from HTML table
        html_content = raw_data["html"]
        soup = BeautifulSoup(html_content, "html.parser")
        schedule_table = soup.find("table", id="schedule")
        if not schedule_table:
            print("No schedule table found in HTML")
            return processed_data

        game_rows = schedule_table.select("tbody tr")
        if not game_rows:
            print("No game rows found in schedule table")
            return processed_data

        for row in game_rows:
            # Extract date
            date_cell = row.select_one("th[data-stat='date_game'] a")
            if not date_cell:
                continue
            date_str = date_cell.text.strip()
            try:
                date = datetime.strptime(date_str, "%a, %b %d, %Y")
            except ValueError as e:
                print(f"Error parsing date {date_str}: {e}")
                continue

            # Extract game data
            try:
                game = {
                    "date": date.isoformat(),
                    "start_time": row.select_one(
                        "td[data-stat='game_start_time']"
                    ).text.strip(),
                    "visitor_team": row.select_one(
                        "td[data-stat='visitor_team_name'] a"
                    ).text.strip(),
                    "visitor_points": int(
                        row.select_one("td[data-stat='visitor_pts']").text.strip() or 0
                    ),
                    "home_team": row.select_one(
                        "td[data-stat='home_team_name'] a"
                    ).text.strip(),
                    "home_points": int(
                        row.select_one("td[data-stat='home_pts']").text.strip() or 0
                    ),
                    "attendance": self._parse_attendance(
                        row.select_one("td[data-stat='attendance']").text.strip()
                    ),
                    "arena": row.select_one("td[data-stat='arena_name']").text.strip(),
                    "box_score_url": "https://www.basketball-reference.com"
                    + row.select_one("td[data-stat='box_score_text'] a")["href"],
                }
                processed_data["games"].append(game)
            except (AttributeError, ValueError) as e:
                print(f"Error processing game row: {e}")
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
