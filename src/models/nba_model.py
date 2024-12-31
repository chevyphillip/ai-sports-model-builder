import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import joblib
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

from data_preparation import prepare_training_data


class NBAPredictor:
    def __init__(self):
        self.moneyline_model = None
        self.spread_model = None
        self.totals_model = None
        self.scaler = StandardScaler()
        self.feature_columns = [
            "home_price",
            "away_price",
            "spread",
            "total",
            "home_rolling_win_prob",
            "away_rolling_win_prob",
            "home_rolling_spread",
            "away_rolling_spread",
        ]

    def prepare_features(self, X):
        """Prepare feature matrix for model input"""
        return self.scaler.transform(X[self.feature_columns])

    def train_models(self, features_df, test_size=0.2):
        """Train all prediction models"""
        # Prepare target variables
        features_df["home_win"] = (
            features_df["home_price"] < features_df["away_price"]
        ).astype(int)
        features_df["cover_spread"] = (features_df["spread"] > 0).astype(int)

        # Split data
        train_df, test_df = train_test_split(
            features_df, test_size=test_size, random_state=42
        )

        # Prepare features
        X_train = self.scaler.fit_transform(train_df[self.feature_columns])
        X_test = self.scaler.transform(test_df[self.feature_columns])

        # Train moneyline model
        print("\nTraining moneyline model...")
        self.moneyline_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.moneyline_model.fit(X_train, train_df["home_win"])
        y_pred = self.moneyline_model.predict(X_test)
        print("Moneyline model performance:")
        print(classification_report(test_df["home_win"], y_pred))

        # Train spread model
        print("\nTraining spread model...")
        self.spread_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.spread_model.fit(X_train, train_df["cover_spread"])
        y_pred = self.spread_model.predict(X_test)
        print("Spread model performance:")
        print(classification_report(test_df["cover_spread"], y_pred))

        # Train totals model
        print("\nTraining totals model...")
        self.totals_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.totals_model.fit(X_train, train_df["total"])
        y_pred = self.totals_model.predict(X_test)
        rmse = np.sqrt(mean_squared_error(test_df["total"], y_pred))
        print(f"Totals model RMSE: {rmse:.2f}")

    def save_models(self, directory="models"):
        """Save trained models to disk"""
        os.makedirs(directory, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        joblib.dump(
            self.moneyline_model, f"{directory}/moneyline_model_{timestamp}.joblib"
        )
        joblib.dump(self.spread_model, f"{directory}/spread_model_{timestamp}.joblib")
        joblib.dump(self.totals_model, f"{directory}/totals_model_{timestamp}.joblib")
        joblib.dump(self.scaler, f"{directory}/scaler_{timestamp}.joblib")

    def load_models(self, directory="models"):
        """Load most recent models from disk"""
        moneyline_models = sorted(
            [f for f in os.listdir(directory) if f.startswith("moneyline_model")]
        )
        spread_models = sorted(
            [f for f in os.listdir(directory) if f.startswith("spread_model")]
        )
        totals_models = sorted(
            [f for f in os.listdir(directory) if f.startswith("totals_model")]
        )
        scalers = sorted([f for f in os.listdir(directory) if f.startswith("scaler")])

        if not all([moneyline_models, spread_models, totals_models, scalers]):
            raise ValueError("Not all required models found in directory")

        self.moneyline_model = joblib.load(f"{directory}/{moneyline_models[-1]}")
        self.spread_model = joblib.load(f"{directory}/{spread_models[-1]}")
        self.totals_model = joblib.load(f"{directory}/{totals_models[-1]}")
        self.scaler = joblib.load(f"{directory}/{scalers[-1]}")

    def predict_upcoming_games(self, games_df):
        """Make predictions for upcoming games"""
        if not all([self.moneyline_model, self.spread_model, self.totals_model]):
            raise ValueError("Models not trained or loaded")

        X = self.prepare_features(games_df)

        predictions = []
        for i, game in games_df.iterrows():
            game_pred = {
                "game_id": game["game_id"],
                "commence_time": game["commence_time"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "current_home_price": game["home_price"],
                "current_away_price": game["away_price"],
                "current_spread": game["spread"],
                "current_total": game["total"],
                "predicted_winner": (
                    game["home_team"]
                    if self.moneyline_model.predict_proba([X[i]])[0][1] > 0.5
                    else game["away_team"]
                ),
                "win_probability": max(self.moneyline_model.predict_proba([X[i]])[0]),
                "predicted_spread_cover": (
                    "Home" if self.spread_model.predict([X[i]])[0] == 1 else "Away"
                ),
                "spread_probability": max(self.spread_model.predict_proba([X[i]])[0]),
                "predicted_total": self.totals_model.predict([X[i]])[0],
            }
            predictions.append(game_pred)

        return pd.DataFrame(predictions)


def get_upcoming_games():
    """Fetch upcoming NBA games from The Odds API"""
    load_dotenv()
    api_key = os.getenv("ODDS_API_KEY")

    url = f"https://api.the-odds-api.com/v4/sports/basketball_nba/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": "h2h,spreads,totals",
        "oddsFormat": "decimal",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        games = []
        for event in response.json():
            game = {
                "game_id": event["id"],
                "commence_time": event["commence_time"],
                "home_team": event["home_team"],
                "away_team": event["away_team"],
            }

            # Get consensus odds
            for bookmaker in event["bookmakers"]:
                if bookmaker["key"] == "fanduel":  # Using FanDuel as primary bookmaker
                    for market in bookmaker["markets"]:
                        if market["key"] == "h2h":
                            for outcome in market["outcomes"]:
                                if outcome["name"] == game["home_team"]:
                                    game["home_price"] = outcome["price"]
                                else:
                                    game["away_price"] = outcome["price"]
                        elif market["key"] == "spreads":
                            for outcome in market["outcomes"]:
                                if outcome["name"] == game["home_team"]:
                                    game["spread"] = outcome["point"]
                        elif market["key"] == "totals":
                            game["total"] = market["outcomes"][0]["point"]

            games.append(game)

        return pd.DataFrame(games)

    except Exception as e:
        print(f"Error fetching upcoming games: {e}")
        return pd.DataFrame()


def format_predictions(predictions_df):
    """Format predictions into a nice display table"""
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", None)

    display_df = predictions_df.copy()
    display_df["commence_time"] = pd.to_datetime(
        display_df["commence_time"]
    ).dt.strftime("%Y-%m-%d %H:%M")
    display_df["win_probability"] = (display_df["win_probability"] * 100).round(
        1
    ).astype(str) + "%"
    display_df["spread_probability"] = (display_df["spread_probability"] * 100).round(
        1
    ).astype(str) + "%"
    display_df["predicted_total"] = display_df["predicted_total"].round(1)

    columns = [
        "commence_time",
        "home_team",
        "away_team",
        "predicted_winner",
        "win_probability",
        "predicted_spread_cover",
        "spread_probability",
        "predicted_total",
    ]

    return display_df[columns]


def main():
    # Prepare training data
    print("Preparing training data...")
    features_df = prepare_training_data()

    # Initialize and train models
    predictor = NBAPredictor()
    predictor.train_models(features_df)

    # Save models
    predictor.save_models()

    # Get upcoming games
    print("\nFetching upcoming games...")
    upcoming_games = get_upcoming_games()

    if len(upcoming_games) > 0:
        # Make predictions
        print("\nMaking predictions...")
        predictions = predictor.predict_upcoming_games(upcoming_games)

        # Display formatted predictions
        print("\nPredictions for upcoming games:")
        print(format_predictions(predictions))
    else:
        print("No upcoming games found")


if __name__ == "__main__":
    main()
