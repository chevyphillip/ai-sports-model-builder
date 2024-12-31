"""
NBA Game Data Pipeline

This module handles loading and preprocessing of NBA game data for model training.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, List
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class NBADataPipeline:
    def __init__(self, db_url: str):
        """Initialize the data pipeline with database connection.

        Args:
            db_url: Database connection URL
        """
        self.engine = create_engine(db_url)

    def load_historical_games(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Load historical NBA games data from database.

        Args:
            start_date: Start date for data loading
            end_date: End date for data loading

        Returns:
            DataFrame containing historical games data
        """
        query = text(
            """
            SELECT *
            FROM nba_game_lines.clean_game_odds
            WHERE commence_time BETWEEN :start_date AND :end_date
            ORDER BY commence_time
            """
        )

        with self.engine.connect() as conn:
            df = pd.read_sql(
                query, conn, params={"start_date": start_date, "end_date": end_date}
            )

        return df

    def calculate_team_stats(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate team statistics based on historical games.

        Args:
            games_df: DataFrame with game data

        Returns:
            DataFrame with team statistics
        """
        # Sort games by start time to calculate rolling stats
        games_df = games_df.sort_values("commence_time")

        # Initialize stats dictionary
        team_stats = {}

        # Calculate stats for each team
        for team in games_df["home_team"].unique():
            # Get all games for the team
            team_games = games_df[
                (games_df["home_team"] == team) | (games_df["away_team"] == team)
            ]

            # Calculate average odds for the team
            home_games = team_games[team_games["home_team"] == team]
            away_games = team_games[team_games["away_team"] == team]

            # Calculate average home odds
            avg_home_odds = (
                home_games["home_price"].mean() if not home_games.empty else 0
            )
            avg_home_spread = home_games["spread"].mean() if not home_games.empty else 0

            # Calculate average away odds
            avg_away_odds = (
                away_games["away_price"].mean() if not away_games.empty else 0
            )
            avg_away_spread = away_games["spread"].mean() if not away_games.empty else 0

            # Store stats
            team_stats[team] = {
                "avg_home_odds": avg_home_odds,
                "avg_away_odds": avg_away_odds,
                "avg_home_spread": avg_home_spread,
                "avg_away_spread": avg_away_spread,
                "total_games": len(team_games),
            }

        return pd.DataFrame.from_dict(team_stats, orient="index")

    def prepare_features(
        self, games_df: pd.DataFrame, stats_df: pd.DataFrame
    ) -> Dict[str, Tuple[pd.DataFrame, pd.Series]]:
        """
        Prepare features for model training.

        Args:
            games_df: DataFrame with game data
            stats_df: DataFrame with team statistics

        Returns:
            Dictionary mapping prediction tasks to (X, y) tuples
        """
        datasets = {}

        # Prepare moneyline dataset
        moneyline_games = games_df[games_df["has_moneyline"] == True]

        if len(moneyline_games) > 0:
            X_moneyline = []
            y_moneyline = []

            for _, game in moneyline_games.iterrows():
                home_team = game["home_team"]
                away_team = game["away_team"]

                home_stats = stats_df.loc[home_team]
                away_stats = stats_df.loc[away_team]

                feature_vector = [
                    home_stats["avg_home_odds"],
                    home_stats["avg_away_odds"],
                    home_stats["avg_home_spread"],
                    home_stats["avg_away_spread"],
                    home_stats["total_games"],
                    away_stats["avg_home_odds"],
                    away_stats["avg_away_odds"],
                    away_stats["avg_home_spread"],
                    away_stats["avg_away_spread"],
                    away_stats["total_games"],
                ]

                # Convert American odds to probability
                home_prob = (
                    1 / (1 + np.exp(game["home_price"] / 100))
                    if game["home_price"] > 0
                    else np.exp(-game["home_price"] / 100)
                    / (1 + np.exp(-game["home_price"] / 100))
                )
                y_moneyline.append(1 if home_prob > 0.5 else 0)
                X_moneyline.append(feature_vector)

            datasets["moneyline"] = (pd.DataFrame(X_moneyline), pd.Series(y_moneyline))

        # Prepare spread dataset
        spread_games = games_df[games_df["has_spread"] == True]

        if len(spread_games) > 0:
            X_spread = []
            y_spread = []

            for _, game in spread_games.iterrows():
                home_team = game["home_team"]
                away_team = game["away_team"]

                home_stats = stats_df.loc[home_team]
                away_stats = stats_df.loc[away_team]

                feature_vector = [
                    home_stats["avg_home_odds"],
                    home_stats["avg_away_odds"],
                    home_stats["avg_home_spread"],
                    home_stats["avg_away_spread"],
                    home_stats["total_games"],
                    away_stats["avg_home_odds"],
                    away_stats["avg_away_odds"],
                    away_stats["avg_home_spread"],
                    away_stats["avg_away_spread"],
                    away_stats["total_games"],
                ]

                y_spread.append(game["spread"])
                X_spread.append(feature_vector)

            datasets["spread"] = (pd.DataFrame(X_spread), pd.Series(y_spread))

        # Prepare totals dataset
        totals_games = games_df[games_df["has_totals"] == True]

        if len(totals_games) > 0:
            X_totals = []
            y_totals = []

            for _, game in totals_games.iterrows():
                home_team = game["home_team"]
                away_team = game["away_team"]

                home_stats = stats_df.loc[home_team]
                away_stats = stats_df.loc[away_team]

                feature_vector = [
                    home_stats["avg_home_odds"],
                    home_stats["avg_away_odds"],
                    home_stats["avg_home_spread"],
                    home_stats["avg_away_spread"],
                    home_stats["total_games"],
                    away_stats["avg_home_odds"],
                    away_stats["avg_away_odds"],
                    away_stats["avg_home_spread"],
                    away_stats["avg_away_spread"],
                    away_stats["total_games"],
                ]

                y_totals.append(game["total"])
                X_totals.append(feature_vector)

            datasets["total"] = (pd.DataFrame(X_totals), pd.Series(y_totals))

        if not datasets:
            raise ValueError("No valid samples found for any prediction task")

        return datasets

    def _calculate_rest_days(
        self, games_df: pd.DataFrame, team: str, game_time: datetime
    ) -> int:
        """Calculate days of rest for a team before a game.

        Args:
            games_df: DataFrame containing historical games
            team: Team to calculate rest days for
            game_time: Time of the game

        Returns:
            Number of days of rest
        """
        # Get team's previous game
        prev_game = (
            games_df[
                ((games_df["home_team"] == team) | (games_df["away_team"] == team))
                & (games_df["start_time"] < game_time)
            ]
            .sort_values("start_time")
            .iloc[-1]
        )

        # Calculate days between games
        return (game_time - prev_game["start_time"]).days

    def split_data(
        self,
        datasets: Dict[str, Tuple[pd.DataFrame, pd.Series]],
        test_size: float = 0.2,
    ) -> Dict[str, Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]]:
        """Split data into training and testing sets.

        Args:
            datasets: Dictionary of (X, y) tuples for each prediction task
            test_size: Proportion of data to use for testing

        Returns:
            Dictionary mapping tasks to (X_train, X_test, y_train, y_test) tuples
        """
        split_datasets = {}

        for task, (X, y) in datasets.items():
            split_idx = int(len(X) * (1 - test_size))

            X_train = X.iloc[:split_idx]
            X_test = X.iloc[split_idx:]
            y_train = y.iloc[:split_idx]
            y_test = y.iloc[split_idx:]

            split_datasets[task] = (X_train, X_test, y_train, y_test)

        return split_datasets
