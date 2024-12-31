import os
import pandas as pd
from firecrawl import FirecrawlApp
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()


class HistoricalScoresCollector:
    """Class to collect historical NBA game scores from basketball-reference.com"""

    MONTHS = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]

    def __init__(self, api_key: str, supabase_client: Client):
        """Initialize the collector with API key and Supabase client"""
        self.api_key = api_key
        self.supabase = supabase_client

    def fetch_basketball_reference_data(self, year: int, month: int) -> pd.DataFrame:
        """
        Fetch NBA game data from Basketball Reference for a specific year and month.
        """
        try:
            # Format the URL
            url = f"https://www.basketball-reference.com/leagues/NBA_{year}_games-{self.MONTHS[month-1].lower()}.html"

            # Initialize FireCrawl with API key
            firecrawl = FirecrawlApp(api_key=self.api_key)

            # Scrape the URL
            response = firecrawl.scrape_url(url)

            if not response or not response.get("html"):
                print("No HTML content found in scrape result")
                print(f"Response: {response}")
                return pd.DataFrame()

            html_content = response["html"]

            # Parse the HTML content using pandas
            dfs = pd.read_html(html_content, attrs={"id": "schedule"})

            if not dfs:
                print(f"No schedule table found for {self.MONTHS[month-1]} {year}")
                return pd.DataFrame()

            # Get the schedule table
            df = dfs[0]

            # Convert date strings to datetime objects
            df["Date"] = pd.to_datetime(df["Date"])

            # Rename columns to match our database schema
            column_mapping = {
                "Date": "date",
                "Visitor/Neutral": "away_team",
                "Home/Neutral": "home_team",
                "PTS": "away_score",
                "PTS.1": "home_score",
                "Attend.": "attendance",
                "Arena": "arena",
                "Notes": "notes",
            }

            df = df.rename(columns=column_mapping)

            # Select only the columns we need
            df = df[
                [
                    "date",
                    "away_team",
                    "home_team",
                    "away_score",
                    "home_score",
                    "attendance",
                    "arena",
                    "notes",
                ]
            ]

            return df

        except Exception as e:
            print(f"Error fetching data from basketball-reference: {str(e)}")
            return pd.DataFrame()

    def process_month(self, year: int, month: int) -> None:
        """
        Process a specific month of NBA games.
        """
        print(f"Processing {self.MONTHS[month-1]} {year}")

        # Fetch data from basketball-reference
        df = self.fetch_basketball_reference_data(year, month)

        if df.empty:
            print(f"No data found for {self.MONTHS[month-1]} {year}")
            return

        print(f"Found {len(df)} games")

        # Insert data into Supabase
        for _, row in df.iterrows():
            game_data = {
                "date": row["date"].strftime("%Y-%m-%d"),
                "away_team": row["away_team"],
                "home_team": row["home_team"],
                "away_score": row["away_score"],
                "home_score": row["home_score"],
                "attendance": (
                    row["attendance"] if pd.notna(row["attendance"]) else None
                ),
                "arena": row["arena"] if pd.notna(row["arena"]) else None,
                "notes": row["notes"] if pd.notna(row["notes"]) else None,
            }

            try:
                data = (
                    self.supabase.table("game_results")
                    .schema("nba_game_lines")
                    .insert(game_data)
                    .execute()
                )
                print(
                    f"Inserted game: {game_data['away_team']} @ {game_data['home_team']} on {game_data['date']}"
                )
            except Exception as e:
                print(f"Error inserting game data: {str(e)}")
                continue


def test_run():
    """Test run for December 2023"""
    print("\nEnvironment variables:")
    print(f"FIRECRAWL_API_KEY: {'*' * len(os.getenv('FIRECRAWL_API_KEY', ''))}")

    # Get environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY"
    )  # Use service role key for database operations
    firecrawl_key = os.getenv("FIRECRAWL_API_KEY")

    if not all([supabase_url, supabase_key, firecrawl_key]):
        print("Error: Required environment variables are not set")
        return

    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)

        # Initialize collector
        collector = HistoricalScoresCollector(
            api_key=firecrawl_key, supabase_client=supabase
        )

        print("\nRunning test for December 2023...")
        collector.process_month(2023, 12)

        # Get total count of game results
        data = (
            collector.supabase.table("game_results")
            .schema("nba_game_lines")
            .select("*")
            .execute()
        )
        print(f"\nTotal game results in database: {len(data.data)}")

    except Exception as e:
        print(f"Error: {str(e)}")
        return


if __name__ == "__main__":
    test_run()
