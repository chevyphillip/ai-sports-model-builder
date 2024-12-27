import requests
import logging
from typing import Dict, List, Optional
from src.config.config import ODDS_API_KEY, ODDS_API_BASE_URL

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OddsAPIClient:
    def __init__(self):
        self.api_key = ODDS_API_KEY
        self.base_url = ODDS_API_BASE_URL

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make a request to the Odds API
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            params["apiKey"] = self.api_key

            response = requests.get(url, params=params)
            response.raise_for_status()

            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Odds API: {str(e)}")
            return None

    def get_sports(self) -> List[Dict]:
        """
        Get all available sports
        """
        return self._make_request("sports", {})

    def get_odds(
        self, sport: str, regions: str = "us", markets: str = "h2h,spreads,totals"
    ) -> Optional[Dict]:
        """
        Get odds for a specific sport
        """
        params = {"sport": sport, "regions": regions, "markets": markets}
        return self._make_request("sports/{sport}/odds", params)

    def get_scores(self, sport: str, daysFrom: int = 1) -> Optional[Dict]:
        """
        Get scores for a specific sport
        """
        params = {"sport": sport, "daysFrom": daysFrom}
        return self._make_request("sports/{sport}/scores", params)


# Usage example:
if __name__ == "__main__":
    client = OddsAPIClient()
    sports = client.get_sports()
    if sports:
        logger.info(f"Available sports: {sports}")
