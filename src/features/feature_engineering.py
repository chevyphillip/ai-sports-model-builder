import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
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


class FeatureEngineering:
    def __init__(self):
        """Initialize the feature engineering pipeline"""
        self.engine = create_engine(DATABASE_URL)

    def get_team_historical_stats(
        self, team_id: int, before_date: datetime, lookback_games: int = 10
    ) -> pd.DataFrame:
        """Get historical team performance stats for feature creation"""
        query = """
        WITH team_games AS (
            -- Get games where team was home
            SELECT 
                g.commence_time,
                g.home_team_id as team_id,
                cgo.home_price as price,
                cgo.spread,
                CASE 
                    WHEN cgo.spread < 0 THEN 1  -- Favored
                    WHEN cgo.spread > 0 THEN 0  -- Underdog
                    ELSE 0.5  -- Pick'em
                END as was_favored
            FROM nba_game_lines.games g
            JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
            WHERE g.home_team_id = :team_id
            AND g.commence_time < :before_date
            
            UNION ALL
            
            -- Get games where team was away
            SELECT 
                g.commence_time,
                g.away_team_id as team_id,
                cgo.away_price as price,
                -cgo.spread as spread,  -- Negate spread for away games
                CASE 
                    WHEN cgo.spread > 0 THEN 1  -- Favored
                    WHEN cgo.spread < 0 THEN 0  -- Underdog
                    ELSE 0.5  -- Pick'em
                END as was_favored
            FROM nba_game_lines.games g
            JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
            WHERE g.away_team_id = :team_id
            AND g.commence_time < :before_date
        )
        SELECT 
            team_id,
            AVG(price) as avg_price,
            AVG(spread) as avg_spread,
            AVG(was_favored) as favored_ratio,
            COUNT(*) as num_games
        FROM (
            SELECT *
            FROM team_games
            ORDER BY commence_time DESC
            LIMIT :lookback_games
        ) recent_games
        GROUP BY team_id
        """

        df = pd.read_sql(
            query,
            self.engine,
            params={
                "team_id": team_id,
                "before_date": before_date,
                "lookback_games": lookback_games,
            },
        )
        return df

    def get_head_to_head_stats(
        self,
        team1_id: int,
        team2_id: int,
        before_date: datetime,
        lookback_games: int = 5,
    ) -> pd.DataFrame:
        """Get head-to-head matchup statistics"""
        query = """
        WITH h2h_games AS (
            SELECT 
                g.commence_time,
                g.home_team_id,
                g.away_team_id,
                cgo.home_price,
                cgo.away_price,
                cgo.spread,
                cgo.total
            FROM nba_game_lines.games g
            JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
            WHERE (g.home_team_id = :team1_id AND g.away_team_id = :team2_id)
               OR (g.home_team_id = :team2_id AND g.away_team_id = :team1_id)
            AND g.commence_time < :before_date
            ORDER BY g.commence_time DESC
            LIMIT :lookback_games
        )
        SELECT 
            COUNT(*) as num_matchups,
            AVG(CASE 
                WHEN home_team_id = :team1_id THEN spread
                ELSE -spread
            END) as avg_spread_team1,
            AVG(total) as avg_total
        FROM h2h_games
        """

        df = pd.read_sql(
            query,
            self.engine,
            params={
                "team1_id": team1_id,
                "team2_id": team2_id,
                "before_date": before_date,
                "lookback_games": lookback_games,
            },
        )
        return df

    def get_odds_movement_features(self, game_id: int) -> pd.DataFrame:
        """Get features related to odds movement for a game"""
        query = """
        WITH odds_changes AS (
            SELECT 
                game_id,
                market_type,
                timestamp,
                home_price,
                away_price,
                spread,
                total,
                LAG(home_price) OVER (PARTITION BY game_id, market_type ORDER BY timestamp) as prev_home_price,
                LAG(away_price) OVER (PARTITION BY game_id, market_type ORDER BY timestamp) as prev_away_price,
                LAG(spread) OVER (PARTITION BY game_id, market_type ORDER BY timestamp) as prev_spread,
                LAG(total) OVER (PARTITION BY game_id, market_type ORDER BY timestamp) as prev_total
            FROM nba_game_lines.game_odds
            WHERE game_id = :game_id
        )
        SELECT 
            market_type,
            COUNT(*) as num_updates,
            AVG(ABS(COALESCE(home_price - prev_home_price, 0))) as avg_home_price_movement,
            AVG(ABS(COALESCE(away_price - prev_away_price, 0))) as avg_away_price_movement,
            AVG(ABS(COALESCE(spread - prev_spread, 0))) as avg_spread_movement,
            AVG(ABS(COALESCE(total - prev_total, 0))) as avg_total_movement
        FROM odds_changes
        GROUP BY market_type
        """

        df = pd.read_sql(query, self.engine, params={"game_id": game_id})
        return df

    def get_current_game_odds(
        self, target_datetime: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get current odds for games at a specific time"""
        if target_datetime is None:
            target_datetime = datetime.now()

        query = """
        SELECT 
            g.id as game_id,
            g.commence_time,
            ht.name as home_team,
            at.name as away_team,
            cgo.home_price,
            cgo.away_price,
            cgo.spread,
            cgo.total,
            cgo.over_price,
            cgo.under_price
        FROM nba_game_lines.games g
        JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
        JOIN nba_game_lines.nba_teams ht ON g.home_team_id = ht.id
        JOIN nba_game_lines.nba_teams at ON g.away_team_id = at.id
        WHERE DATE(g.commence_time) = DATE(:target_date)
        AND EXTRACT(HOUR FROM g.commence_time) = :target_hour
        AND EXTRACT(MINUTE FROM g.commence_time) = :target_minute
        """

        df = pd.read_sql(
            query,
            self.engine,
            params={
                "target_date": target_datetime.date(),
                "target_hour": target_datetime.hour,
                "target_minute": target_datetime.minute,
            },
        )
        return df

    def create_game_features(
        self, game_id: int, home_team_id: int, away_team_id: int, game_time: datetime
    ) -> pd.DataFrame:
        """Create all features for a specific game"""
        # Get team historical stats
        home_stats = self.get_team_historical_stats(home_team_id, game_time)
        away_stats = self.get_team_historical_stats(away_team_id, game_time)

        # Get head-to-head stats
        h2h_stats = self.get_head_to_head_stats(home_team_id, away_team_id, game_time)

        # Get odds movement features
        odds_movement = self.get_odds_movement_features(game_id)

        # Combine all features
        features = {
            "game_id": game_id,
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            "game_time": game_time,
        }

        # Add team stats features
        if not home_stats.empty:
            features.update(
                {
                    "home_avg_price": home_stats.iloc[0]["avg_price"],
                    "home_avg_spread": home_stats.iloc[0]["avg_spread"],
                    "home_favored_ratio": home_stats.iloc[0]["favored_ratio"],
                }
            )

        if not away_stats.empty:
            features.update(
                {
                    "away_avg_price": away_stats.iloc[0]["avg_price"],
                    "away_avg_spread": away_stats.iloc[0]["avg_spread"],
                    "away_favored_ratio": away_stats.iloc[0]["favored_ratio"],
                }
            )

        # Add head-to-head features
        if not h2h_stats.empty:
            features.update(
                {
                    "h2h_num_matchups": h2h_stats.iloc[0]["num_matchups"],
                    "h2h_avg_spread": h2h_stats.iloc[0]["avg_spread_team1"],
                    "h2h_avg_total": h2h_stats.iloc[0]["avg_total"],
                }
            )

        # Add odds movement features if available
        if not odds_movement.empty:
            for _, row in odds_movement.iterrows():
                market = row["market_type"]
                features.update(
                    {
                        f"{market}_num_updates": row["num_updates"],
                        f"{market}_avg_home_movement": row["avg_home_price_movement"],
                        f"{market}_avg_away_movement": row["avg_away_price_movement"],
                        f"{market}_avg_spread_movement": row["avg_spread_movement"],
                        f"{market}_avg_total_movement": row["avg_total_movement"],
                    }
                )

        return pd.DataFrame([features])


def main():
    """Test the feature engineering pipeline"""
    fe = FeatureEngineering()

    # Get current games
    target_time = datetime(2024, 1, 1, 15, 10)  # 3:10 PM EST
    current_games = fe.get_current_game_odds(target_time)

    if current_games.empty:
        print("No games found at the specified time.")
        return

    print("\nCurrent Games:")
    print(current_games)

    # Create features for each game
    all_features = []
    for _, game in current_games.iterrows():
        features = fe.create_game_features(
            game["game_id"],
            game["home_team_id"],
            game["away_team_id"],
            game["commence_time"],
        )
        all_features.append(features)

    if all_features:
        features_df = pd.concat(all_features, ignore_index=True)
        print("\nGenerated Features:")
        print(features_df)


if __name__ == "__main__":
    main()
