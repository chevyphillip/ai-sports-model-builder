import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import seaborn as sns
import matplotlib.pyplot as plt
from urllib.parse import quote_plus

# Load environment variables
load_dotenv()

# Database connection parameters
DB_USER = os.getenv("SUPABASE_DB_USER")
DB_PASSWORD = quote_plus(os.getenv("SUPABASE_DB_PASSWORD"))
DB_HOST = os.getenv("SUPABASE_DB_HOST")
DB_PORT = os.getenv("SUPABASE_DB_PORT")
DB_NAME = os.getenv("SUPABASE_DB_NAME")

# Create database connection URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def connect_to_db():
    """Establish connection to the database"""
    try:
        engine = create_engine(DATABASE_URL)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def analyze_odds_distribution(engine):
    """Analyze the distribution of odds and spreads"""
    try:
        # Query to get odds data with team names
        query = """
        SELECT 
            g.commence_time,
            ht.name as home_team,
            at.name as away_team,
            cgo.home_price,
            cgo.away_price,
            cgo.spread,
            cgo.total,
            cgo.over_price,
            cgo.under_price
        FROM nba_game_lines.clean_game_odds cgo
        JOIN nba_game_lines.games g ON cgo.id = g.id
        JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
        JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
        WHERE cgo.home_price IS NOT NULL 
            AND cgo.away_price IS NOT NULL
        ORDER BY g.commence_time
        """

        df = pd.read_sql(query, engine)

        print("\nOdds Analysis:")
        print(f"Total games with odds: {len(df)}")

        # Analyze home/away price distribution
        print("\nMoneyline Odds Distribution:")
        print(df[["home_price", "away_price"]].describe())

        # Analyze spread distribution
        print("\nSpread Distribution:")
        print(df["spread"].describe())

        # Analyze totals distribution
        print("\nTotals Distribution:")
        print(df["total"].describe())

        # Calculate implied probabilities
        df["home_implied_prob"] = 1 / df["home_price"]
        df["away_implied_prob"] = 1 / df["away_price"]

        print("\nImplied Probability Distribution:")
        print(df[["home_implied_prob", "away_implied_prob"]].describe())

        return df

    except Exception as e:
        print(f"Error analyzing odds distribution: {e}")
        return None


def analyze_odds_by_team(engine):
    """Analyze odds patterns for each team"""
    try:
        query = """
        WITH team_odds AS (
            -- Home games
            SELECT 
                ht.name as team_name,
                'home' as game_location,
                cgo.home_price as price,
                cgo.spread
            FROM nba_game_lines.clean_game_odds cgo
            JOIN nba_game_lines.games g ON cgo.id = g.id
            JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
            WHERE cgo.home_price IS NOT NULL
            
            UNION ALL
            
            -- Away games
            SELECT 
                at.name as team_name,
                'away' as game_location,
                cgo.away_price as price,
                -cgo.spread as spread  -- Negate spread for away teams
            FROM nba_game_lines.clean_game_odds cgo
            JOIN nba_game_lines.games g ON cgo.id = g.id
            JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
            WHERE cgo.away_price IS NOT NULL
        )
        SELECT 
            team_name,
            game_location,
            COUNT(*) as num_games,
            AVG(price) as avg_price,
            AVG(spread) as avg_spread,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM team_odds
        GROUP BY team_name, game_location
        ORDER BY team_name, game_location
        """

        df = pd.read_sql(query, engine)
        print("\nTeam-by-Team Odds Analysis:")
        print(df)

        return df

    except Exception as e:
        print(f"Error analyzing team odds: {e}")
        return None


def analyze_odds_movement(engine):
    """Analyze how odds change over time for games"""
    try:
        query = """
        SELECT 
            g.game_id,
            ht.name as home_team,
            at.name as away_team,
            go.timestamp,
            go.market_type,
            go.home_price,
            go.away_price,
            go.spread,
            go.total,
            b.name as bookmaker
        FROM nba_game_lines.game_odds go
        JOIN nba_game_lines.games g ON go.game_id = g.id
        JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
        JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
        JOIN nba_game_lines.bookmakers b ON go.bookmaker_id = b.id
        ORDER BY g.game_id, go.timestamp
        """

        df = pd.read_sql(query, engine)

        # Analyze odds movement patterns
        print("\nOdds Movement Analysis:")

        # Calculate time until game for each odds entry
        df["timestamp"] = pd.to_datetime(df["timestamp"])

        # Group by game and market type to analyze movement
        movement_stats = (
            df.groupby(["game_id", "market_type"])
            .agg(
                {
                    "home_price": ["count", "std"],
                    "away_price": ["count", "std"],
                    "spread": ["count", "std"],
                    "total": ["count", "std"],
                }
            )
            .reset_index()
        )

        print("\nOdds Movement Statistics:")
        print(movement_stats.describe())

        return df

    except Exception as e:
        print(f"Error analyzing odds movement: {e}")
        return None


def main():
    """Main function to analyze odds data"""
    engine = connect_to_db()
    if not engine:
        return

    print("Analyzing NBA betting odds data...")

    # Analyze overall odds distribution
    odds_dist_df = analyze_odds_distribution(engine)

    # Analyze team-specific patterns
    team_odds_df = analyze_odds_by_team(engine)

    # Analyze odds movement
    odds_movement_df = analyze_odds_movement(engine)

    if odds_dist_df is not None:
        # Create visualizations
        plt.figure(figsize=(12, 6))

        # Plot spread distribution
        plt.subplot(1, 2, 1)
        sns.histplot(data=odds_dist_df, x="spread", bins=30)
        plt.title("Distribution of Spreads")
        plt.xlabel("Spread (points)")

        # Plot totals distribution
        plt.subplot(1, 2, 2)
        sns.histplot(data=odds_dist_df, x="total", bins=30)
        plt.title("Distribution of Totals")
        plt.xlabel("Total Points")

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
