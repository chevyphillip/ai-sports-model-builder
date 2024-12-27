import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import aiohttp
import asyncio
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class FirecrawlClient:
    """Client for interacting with the Firecrawl API"""

    BASE_URL = "https://api.firecrawl.io/v1"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Firecrawl client"""
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Firecrawl API key not found. Please set FIRECRAWL_API_KEY environment variable."
            )

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make a request to the Firecrawl API"""
        url = f"{self.BASE_URL}/{endpoint}"

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(
                method, url, params=params, json=data
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def scrape_nba_game_data(
        self,
        url: str,
        selectors: Dict[str, str],
        wait_for: Optional[str] = None,
        javascript_render: bool = True,
    ) -> Dict:
        """
        Scrape NBA game data from a given URL using specified selectors

        Args:
            url: The URL to scrape
            selectors: Dictionary of CSS selectors to extract data
            wait_for: Optional selector to wait for before scraping
            javascript_render: Whether to render JavaScript (default: True)

        Returns:
            Dictionary containing the scraped data
        """
        data = {"url": url, "selectors": selectors, "javascript": javascript_render}

        if wait_for:
            data["wait_for"] = wait_for

        try:
            result = await self._make_request("POST", "scrape", data=data)
            return result
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}

    async def scrape_multiple_games(
        self,
        urls: List[str],
        selectors: Dict[str, str],
        wait_for: Optional[str] = None,
        javascript_render: bool = True,
        concurrent_limit: int = 5,
    ) -> List[Dict]:
        """
        Scrape multiple NBA game URLs concurrently

        Args:
            urls: List of URLs to scrape
            selectors: Dictionary of CSS selectors to extract data
            wait_for: Optional selector to wait for before scraping
            javascript_render: Whether to render JavaScript
            concurrent_limit: Maximum number of concurrent requests

        Returns:
            List of dictionaries containing the scraped data
        """
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def scrape_with_semaphore(url: str) -> Dict:
            async with semaphore:
                return await self.scrape_nba_game_data(
                    url, selectors, wait_for, javascript_render
                )

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out any errors and log them
        valid_results = []
        for url, result in zip(urls, results):
            if isinstance(result, Exception):
                print(f"Error scraping {url}: {result}")
            else:
                valid_results.append(result)

        return valid_results

    def save_scraped_data(
        self, data: Union[Dict, List[Dict]], output_dir: str, prefix: str = "nba_game"
    ) -> str:
        """
        Save scraped data to a JSON file

        Args:
            data: Scraped data to save
            output_dir: Directory to save the file
            prefix: Prefix for the filename

        Returns:
            Path to the saved file
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        # Save data to file
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        return filepath


# Example usage:
async def main():
    # Initialize client
    client = FirecrawlClient()

    # Example selectors for NBA game data
    selectors = {
        "home_team": ".home-team",
        "away_team": ".away-team",
        "home_score": ".home-score",
        "away_score": ".away-score",
        "game_date": ".game-date",
        "stats_table": ".stats-table",
    }

    # Example URLs (replace with actual NBA game URLs)
    urls = ["https://example.com/nba/game1", "https://example.com/nba/game2"]

    # Scrape multiple games
    results = await client.scrape_multiple_games(
        urls=urls, selectors=selectors, wait_for=".stats-table", javascript_render=True
    )

    # Save results
    output_path = client.save_scraped_data(
        data=results, output_dir="data/raw/nba_games"
    )
    print(f"Saved scraped data to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
