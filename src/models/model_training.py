import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report
import joblib
from datetime import datetime
from typing import Dict, Tuple
from src.features.feature_engineering import FeatureEngineering


class ModelTraining:
    def __init__(self):
        """Initialize the model training pipeline"""
        self.fe = FeatureEngineering()
        self.models_dir = "models"
        os.makedirs(self.models_dir, exist_ok=True)

        # Initialize models
        self.h2h_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.spread_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.totals_model = RandomForestRegressor(n_estimators=100, random_state=42)

        # Initialize scalers
        self.h2h_scaler = StandardScaler()
        self.spread_scaler = StandardScaler()
        self.totals_scaler = StandardScaler()

    def prepare_training_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Prepare historical data for training"""
        query = """
        WITH historical_games AS (
            SELECT 
                g.id as game_id,
                g.commence_time,
                g.home_team_id,
                g.away_team_id,
                cgo.home_price,
                cgo.away_price,
                cgo.spread,
                cgo.total,
                -- Add actual results here when available
                CASE 
                    WHEN cgo.home_price < cgo.away_price THEN 1  -- Home team won
                    ELSE 0  -- Away team won
                END as home_team_won,  -- Placeholder until we have actual results
                cgo.spread as actual_spread,  -- Placeholder
                cgo.total as actual_total  -- Placeholder
            FROM nba_game_lines.games g
            JOIN nba_game_lines.clean_game_odds cgo ON g.id = cgo.id
            WHERE g.commence_time < CURRENT_TIMESTAMP
            ORDER BY g.commence_time DESC
            LIMIT 1000  -- Adjust based on available data
        )
        SELECT * FROM historical_games
        """

        historical_games = pd.read_sql(query, self.fe.engine)

        # Create features for each historical game
        all_features = []
        for _, game in historical_games.iterrows():
            features = self.fe.create_game_features(
                game["game_id"],
                game["home_team_id"],
                game["away_team_id"],
                game["commence_time"],
            )

            # Add target variables
            features["home_team_won"] = game["home_team_won"]
            features["actual_spread"] = game["actual_spread"]
            features["actual_total"] = game["actual_total"]

            all_features.append(features)

        return pd.concat(all_features, ignore_index=True)

    def train_models(self):
        """Train all three models"""
        # Get training data
        data = self.prepare_training_data()

        # Prepare feature sets
        feature_cols = [
            col
            for col in data.columns
            if col
            not in [
                "game_id",
                "home_team_won",
                "actual_spread",
                "actual_total",
                "game_time",
            ]
        ]

        # Split features and targets
        X = data[feature_cols]
        y_h2h = data["home_team_won"]
        y_spread = data["actual_spread"]
        y_total = data["actual_total"]

        # Split into train and test sets
        X_train, X_test, y_h2h_train, y_h2h_test = train_test_split(
            X, y_h2h, test_size=0.2, random_state=42
        )
        _, _, y_spread_train, y_spread_test = train_test_split(
            X, y_spread, test_size=0.2, random_state=42
        )
        _, _, y_total_train, y_total_test = train_test_split(
            X, y_total, test_size=0.2, random_state=42
        )

        # Scale features
        X_train_h2h = self.h2h_scaler.fit_transform(X_train)
        X_test_h2h = self.h2h_scaler.transform(X_test)

        X_train_spread = self.spread_scaler.fit_transform(X_train)
        X_test_spread = self.spread_scaler.transform(X_test)

        X_train_total = self.totals_scaler.fit_transform(X_train)
        X_test_total = self.totals_scaler.transform(X_test)

        # Train models
        print("Training H2H model...")
        self.h2h_model.fit(X_train_h2h, y_h2h_train)
        h2h_pred = self.h2h_model.predict(X_test_h2h)
        print("H2H Model Performance:")
        print(classification_report(y_h2h_test, h2h_pred))

        print("\nTraining Spread model...")
        self.spread_model.fit(X_train_spread, y_spread_train)
        spread_pred = self.spread_model.predict(X_test_spread)
        spread_rmse = np.sqrt(mean_squared_error(y_spread_test, spread_pred))
        print(f"Spread Model RMSE: {spread_rmse:.2f}")

        print("\nTraining Totals model...")
        self.totals_model.fit(X_train_total, y_total_train)
        total_pred = self.totals_model.predict(X_test_total)
        total_rmse = np.sqrt(mean_squared_error(y_total_test, total_pred))
        print(f"Totals Model RMSE: {total_rmse:.2f}")

        # Save models and scalers
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        joblib.dump(self.h2h_model, f"{self.models_dir}/h2h_model_{timestamp}.joblib")
        joblib.dump(
            self.spread_model, f"{self.models_dir}/spread_model_{timestamp}.joblib"
        )
        joblib.dump(
            self.totals_model, f"{self.models_dir}/totals_model_{timestamp}.joblib"
        )

        joblib.dump(self.h2h_scaler, f"{self.models_dir}/h2h_scaler_{timestamp}.joblib")
        joblib.dump(
            self.spread_scaler, f"{self.models_dir}/spread_scaler_{timestamp}.joblib"
        )
        joblib.dump(
            self.totals_scaler, f"{self.models_dir}/totals_scaler_{timestamp}.joblib"
        )

    def predict_games(self, target_datetime: datetime) -> pd.DataFrame:
        """Make predictions for games at a specific time"""
        # Get current games
        current_games = self.fe.get_current_game_odds(target_datetime)

        if current_games.empty:
            return pd.DataFrame()

        # Create features for each game
        all_predictions = []
        for _, game in current_games.iterrows():
            # Generate features
            features = self.fe.create_game_features(
                game["game_id"],
                game["home_team_id"],
                game["away_team_id"],
                game["commence_time"],
            )

            # Prepare features
            feature_cols = [
                col for col in features.columns if col not in ["game_id", "game_time"]
            ]
            X = features[feature_cols]

            # Scale features
            X_h2h = self.h2h_scaler.transform(X)
            X_spread = self.spread_scaler.transform(X)
            X_total = self.totals_scaler.transform(X)

            # Make predictions
            h2h_prob = self.h2h_model.predict_proba(X_h2h)[0]
            spread_pred = self.spread_model.predict(X_spread)[0]
            total_pred = self.totals_model.predict(X_total)[0]

            # Prepare prediction row
            prediction = {
                "home_team": game["home_team"],
                "away_team": game["away_team"],
                "current_h2h_odds": f"{game['home_price']}/{game['away_price']}",
                "current_spread_line": game["spread"],
                "current_total_line": game["total"],
                "predicted_to_win_team": (
                    game["home_team"] if h2h_prob[1] > 0.5 else game["away_team"]
                ),
                "predicted_spread": spread_pred,
                "predicted_total": total_pred,
                "ai_conf_score": max(h2h_prob),
            }

            all_predictions.append(prediction)

        return pd.DataFrame(all_predictions)


def main():
    """Test the model training pipeline"""
    mt = ModelTraining()

    # Train models
    print("Training models...")
    mt.train_models()

    # Make predictions for today's games
    target_time = datetime(2024, 1, 1, 15, 10)  # 3:10 PM EST
    predictions = mt.predict_games(target_time)

    if not predictions.empty:
        print("\nPredictions for today's games:")
        print(predictions)
    else:
        print("\nNo games found for the specified time.")


if __name__ == "__main__":
    main()
