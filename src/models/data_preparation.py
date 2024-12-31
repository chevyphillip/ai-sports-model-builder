import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus


def get_db_connection():
    """Create database connection"""
    load_dotenv()

    DB_USER = os.getenv("SUPABASE_DB_USER")
    DB_PASSWORD = quote_plus(os.getenv("SUPABASE_DB_PASSWORD"))
    DB_HOST = os.getenv("SUPABASE_DB_HOST")
    DB_PORT = os.getenv("SUPABASE_DB_PORT")
    DB_NAME = os.getenv("SUPABASE_DB_NAME")

    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(DATABASE_URL)


def get_historical_games_with_odds():
    """Get historical games data joined with odds and teams"""
    engine = get_db_connection()

    query = text(
        """
        WITH game_odds_summary AS (
            SELECT 
                g.id as game_id,
                g.commence_time,
                ht.name as home_team,
                at.name as away_team,
                cgo.home_price,
                cgo.away_price,
                cgo.spread,
                cgo.total,
                cgo.has_moneyline,
                cgo.has_spread,
                cgo.has_totals,
                cgo.odds_timestamp
            FROM nba_game_lines.games g
            JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
            JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
            JOIN nba_game_lines.clean_game_odds cgo ON cgo.home_team_id = g.home_team_id 
                AND cgo.away_team_id = g.away_team_id
                AND cgo.commence_time = g.commence_time
            WHERE cgo.odds_timestamp <= g.commence_time  -- Only use odds from before game start
            AND cgo.home_price IS NOT NULL
            AND cgo.away_price IS NOT NULL
            AND cgo.spread IS NOT NULL
            AND cgo.total IS NOT NULL
            AND cgo.has_spread = true
            AND cgo.has_totals = true
            ORDER BY g.commence_time ASC
        )
        SELECT * FROM game_odds_summary
    """
    )

    df = pd.read_sql(query, engine)

    # Drop rows with invalid numeric values
    df = df.dropna(subset=["spread", "total", "home_price", "away_price"])

    return df


def calculate_team_rolling_stats(games_df, window=10):
    """Calculate rolling statistics for each team"""
    # Convert prices to implied probabilities
    games_df["home_implied_prob"] = 1 / games_df["home_price"]
    games_df["away_implied_prob"] = 1 / games_df["away_price"]

    # Create team-specific features
    team_features = {}

    for team in pd.concat([games_df["home_team"], games_df["away_team"]]).unique():
        # Get games where team played
        home_games = games_df[games_df["home_team"] == team].copy()
        away_games = games_df[games_df["away_team"] == team].copy()

        # Calculate rolling averages for home games
        if not home_games.empty:
            home_games["rolling_implied_win_prob"] = (
                home_games["home_implied_prob"]
                .rolling(window=window, min_periods=1)
                .mean()
            )
            home_games["rolling_spread"] = (
                home_games["spread"].rolling(window=window, min_periods=1).mean()
            )

        # Calculate rolling averages for away games
        if not away_games.empty:
            away_games["rolling_implied_win_prob"] = (
                away_games["away_implied_prob"]
                .rolling(window=window, min_periods=1)
                .mean()
            )
            away_games["rolling_spread"] = (
                (-away_games["spread"]).rolling(window=window, min_periods=1).mean()
            )

        # Combine home and away stats
        team_stats = pd.concat(
            [
                (
                    home_games[
                        ["commence_time", "rolling_implied_win_prob", "rolling_spread"]
                    ]
                    if not home_games.empty
                    else pd.DataFrame()
                ),
                (
                    away_games[
                        ["commence_time", "rolling_implied_win_prob", "rolling_spread"]
                    ]
                    if not away_games.empty
                    else pd.DataFrame()
                ),
            ]
        ).sort_values("commence_time")

        if not team_stats.empty:
            # Fill any missing values with defaults
            team_stats = team_stats.fillna(method="ffill").fillna(
                {"rolling_implied_win_prob": 0.5, "rolling_spread": 0}
            )
            team_features[team] = team_stats
        else:
            # Create default stats for teams with no games
            team_features[team] = pd.DataFrame(
                {
                    "commence_time": [pd.Timestamp.min],
                    "rolling_implied_win_prob": [0.5],
                    "rolling_spread": [0],
                }
            )

    return team_features


def prepare_features(games_df, team_features):
    """Prepare feature matrix for model training"""
    features = []

    for _, game in games_df.iterrows():
        home_team = game["home_team"]
        away_team = game["away_team"]
        game_time = pd.to_datetime(game["commence_time"])

        # Get team stats before this game
        home_stats = team_features[home_team][
            team_features[home_team]["commence_time"] < game_time
        ]
        away_stats = team_features[away_team][
            team_features[away_team]["commence_time"] < game_time
        ]

        # Use the most recent stats, or defaults if no previous games
        if not home_stats.empty:
            home_latest = home_stats.iloc[-1]
        else:
            home_latest = pd.Series(
                {"rolling_implied_win_prob": 0.5, "rolling_spread": 0}
            )

        if not away_stats.empty:
            away_latest = away_stats.iloc[-1]
        else:
            away_latest = pd.Series(
                {"rolling_implied_win_prob": 0.5, "rolling_spread": 0}
            )

        game_features = {
            "game_id": game["game_id"],
            "commence_time": game_time,
            "home_team": home_team,
            "away_team": away_team,
            "home_price": game["home_price"],
            "away_price": game["away_price"],
            "spread": game["spread"],
            "total": game["total"],
            "home_rolling_win_prob": home_latest["rolling_implied_win_prob"],
            "away_rolling_win_prob": away_latest["rolling_implied_win_prob"],
            "home_rolling_spread": home_latest["rolling_spread"],
            "away_rolling_spread": away_latest["rolling_spread"],
        }

        features.append(game_features)

    return pd.DataFrame(features)


def prepare_training_data(lookback_window=10):
    """Prepare complete training dataset"""
    # Get historical games and odds
    print("Fetching historical games and odds...")
    games_df = get_historical_games_with_odds()
    print(f"Found {len(games_df)} games with complete odds data")

    # Calculate team statistics
    print("Calculating team rolling statistics...")
    team_features = calculate_team_rolling_stats(games_df, window=lookback_window)

    # Prepare feature matrix
    print("Preparing feature matrix...")
    features_df = prepare_features(games_df, team_features)

    return features_df


if __name__ == "__main__":
    # Test data preparation
    features_df = prepare_training_data()
    print("\nPrepared features shape:", features_df.shape)
    print("\nSample features:")
    print(features_df.head())
    print("\nFeature columns:")
    print(features_df.columns.tolist())
