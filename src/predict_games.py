import os
from datetime import datetime, timedelta
import pytz
from src.models.model_training import ModelTraining


def predict_todays_games():
    """Make predictions for today's NBA games at 3:10 PM EST"""
    # Initialize model training
    mt = ModelTraining()

    # Train models if they don't exist
    models_exist = all(
        os.path.exists(f"models/{model}")
        for model in [
            "h2h_model_latest.joblib",
            "spread_model_latest.joblib",
            "totals_model_latest.joblib",
        ]
    )

    if not models_exist:
        print("Training new models...")
        mt.train_models()

    # Set target time to 3:10 PM EST today
    est = pytz.timezone("US/Eastern")
    now = datetime.now(est)
    target_time = now.replace(hour=15, minute=10, second=0, microsecond=0)

    # Make predictions
    predictions = mt.predict_games(target_time)

    if predictions.empty:
        print(f"No games found for {target_time.strftime('%Y-%m-%d %H:%M %Z')}")
        return

    # Display predictions
    print(f"\nPredictions for games at {target_time.strftime('%Y-%m-%d %H:%M %Z')}:")
    print("\nGame Predictions:")
    print("=" * 100)

    for _, pred in predictions.iterrows():
        print(f"🏀 {pred['home_team']} vs {pred['away_team']}")
        print(f"Current H2H Odds: {pred['current_h2h_odds']}")
        print(f"Current Spread: {pred['current_spread_line']}")
        print(f"Current Total: {pred['current_total_line']}")
        print(f"Predictions:")
        print(
            f"  Winner: {pred['predicted_to_win_team']} (Confidence: {pred['ai_conf_score']:.2%})"
        )
        print(f"  Spread: {pred['predicted_spread']:.1f}")
        print(f"  Total: {pred['predicted_total']:.1f}")
        print("-" * 100)


if __name__ == "__main__":
    predict_todays_games()
