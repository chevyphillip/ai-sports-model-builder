"""Integration tests for the FireCrawl client."""

import os
import pytest
from datetime import datetime
from src.data_collection.firecrawl_client import FireCrawlClient


@pytest.fixture
def client():
    """Create a FireCrawl client instance for testing."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        pytest.skip("FIRECRAWL_API_KEY environment variable not set")
    return FireCrawlClient(api_key=api_key)


def test_generate_nba_schedule_url():
    """Test URL generation for NBA schedule."""
    client = FireCrawlClient(api_key="dummy")

    # Test full season URL
    url = client.generate_nba_schedule_url(2024)
    assert url == "https://www.basketball-reference.com/leagues/NBA_2024_games.html"

    # Test monthly URL
    url = client.generate_nba_schedule_url(2024, "january")
    assert (
        url
        == "https://www.basketball-reference.com/leagues/NBA_2024_games-january.html"
    )


def test_scrape_nba_schedule_local(client):
    """Test NBA schedule scraping using local data."""
    result = client.scrape_nba_schedule(2024, use_local=True)

    assert isinstance(result, dict)
    assert "games" in result
    assert "metadata" in result

    metadata = result["metadata"]
    assert metadata["season_year"] == 2024
    assert metadata["season"] == "2023-24"
    assert isinstance(metadata["scraped_at"], str)

    if result["games"]:
        game = result["games"][0]
        assert isinstance(game["date"], str)
        assert isinstance(game["visitor_team"], str)
        assert isinstance(game["home_team"], str)
        assert isinstance(game["visitor_points"], int)
        assert isinstance(game["home_points"], int)


@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_TESTS"),
    reason="Skipping live API tests. Set RUN_LIVE_TESTS=1 to run.",
)
def test_scrape_nba_schedule_live(client):
    """Test live NBA schedule scraping."""
    current_year = datetime.now().year
    result = client.scrape_nba_schedule(current_year, use_local=False)

    assert isinstance(result, dict)
    assert "games" in result
    assert "metadata" in result

    metadata = result["metadata"]
    assert metadata["season_year"] == current_year
    assert isinstance(metadata["scraped_at"], str)

    if result["games"]:
        game = result["games"][0]
        assert isinstance(game["date"], str)
        assert isinstance(game["visitor_team"], str)
        assert isinstance(game["home_team"], str)
        assert isinstance(game["visitor_points"], int)
        assert isinstance(game["home_points"], int)


def test_save_schedule_data(client, tmp_path):
    """Test saving schedule data to a file."""
    test_data = {
        "games": [
            {
                "date": "2024-01-01T00:00:00",
                "visitor_team": "Team A",
                "home_team": "Team B",
                "visitor_points": 100,
                "home_points": 95,
            }
        ],
        "metadata": {
            "season_year": 2024,
            "season": "2023-24",
            "scraped_at": datetime.now().isoformat(),
        },
    }

    output_dir = str(tmp_path)
    filepath = client.save_schedule_data(test_data, 2024, output_dir)

    assert os.path.exists(filepath)
    assert filepath.endswith(".json")
    assert "nba_schedule_2024_" in filepath
