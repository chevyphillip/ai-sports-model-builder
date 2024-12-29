from src.data_collection.firecrawl_client import FireCrawlClient


def test_month_availability():
    client = FireCrawlClient()
    months = [
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

    print(f"Testing month availability for 2012 season...")

    for month in months:
        data = client.scrape_nba_schedule(2012, month, use_local=False)
        games = data.get("games", [])
        if games:
            print(f"{month.capitalize()}: {len(games)} games found")
        else:
            print(f"{month.capitalize()}: No games found")


if __name__ == "__main__":
    test_month_availability()
