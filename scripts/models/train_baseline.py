"""
Train and evaluate baseline NBA prediction models.
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import json
from dotenv import load_dotenv
from urllib.parse import quote_plus
from sqlalchemy import text

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from src.models.nba.data.pipeline import NBADataPipeline
from src.models.nba.training.baseline_model import NBABaselineModel


def main():
    # Load environment variables
    load_dotenv()

    # Construct database URL with properly encoded password
    db_user = os.getenv("SUPABASE_DB_USER")
    db_password = quote_plus(os.getenv("SUPABASE_DB_PASSWORD"))
    db_host = os.getenv("SUPABASE_DB_HOST")
    db_port = os.getenv("SUPABASE_DB_PORT")
    db_name = os.getenv("SUPABASE_DB_NAME")

    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    # Initialize data pipeline
    pipeline = NBADataPipeline(db_url)

    # Check available data range
    query = text(
        """
        WITH game_stats AS (
            SELECT 
                DATE_TRUNC('month', commence_time) as month,
                COUNT(*) as total_games,
                SUM(CASE WHEN has_moneyline THEN 1 ELSE 0 END) as moneyline_games,
                SUM(CASE WHEN has_spread THEN 1 ELSE 0 END) as spread_games,
                SUM(CASE WHEN has_totals THEN 1 ELSE 0 END) as totals_games
            FROM nba_game_lines.clean_game_odds
            GROUP BY DATE_TRUNC('month', commence_time)
            ORDER BY month
        )
        SELECT 
            MIN(commence_time) as earliest_game,
            MAX(commence_time) as latest_game,
            COUNT(*) as total_games,
            SUM(CASE WHEN has_moneyline THEN 1 ELSE 0 END) as moneyline_games,
            SUM(CASE WHEN has_spread THEN 1 ELSE 0 END) as spread_games,
            SUM(CASE WHEN has_totals THEN 1 ELSE 0 END) as totals_games,
            (SELECT json_agg(row_to_json(m)) 
             FROM (
                 SELECT 
                     month,
                     gs.total_games,
                     gs.moneyline_games,
                     gs.spread_games,
                     gs.totals_games,
                     ROUND(100.0 * gs.moneyline_games / gs.total_games, 2) as moneyline_pct,
                     ROUND(100.0 * gs.spread_games / gs.total_games, 2) as spread_pct,
                     ROUND(100.0 * gs.totals_games / gs.total_games, 2) as totals_pct
                 FROM game_stats gs
             ) m
            ) as monthly_stats
        FROM nba_game_lines.clean_game_odds;
        """
    )

    with pipeline.engine.connect() as conn:
        result = pd.read_sql(query, conn)
        print("\nAvailable Data Range:")
        print(f"Earliest Game: {result['earliest_game'].iloc[0]}")
        print(f"Latest Game: {result['latest_game'].iloc[0]}")
        print(f"\nOverall Statistics:")
        print(f"Total Games: {result['total_games'].iloc[0]}")
        print(
            f"Games with Moneyline: {result['moneyline_games'].iloc[0]} ({result['moneyline_games'].iloc[0]/result['total_games'].iloc[0]*100:.1f}%)"
        )
        print(
            f"Games with Spread: {result['spread_games'].iloc[0]} ({result['spread_games'].iloc[0]/result['total_games'].iloc[0]*100:.1f}%)"
        )
        print(
            f"Games with Totals: {result['totals_games'].iloc[0]} ({result['totals_games'].iloc[0]/result['total_games'].iloc[0]*100:.1f}%)"
        )

        print("\nMonthly Statistics:")
        monthly_stats = pd.DataFrame(result["monthly_stats"].iloc[0])
        pd.set_option("display.max_rows", None)
        print(
            monthly_stats[
                ["month", "total_games", "moneyline_pct", "spread_pct", "totals_pct"]
            ].to_string(index=False)
        )

    # Check data by bookmaker
    bookmaker_query = text(
        """
        WITH latest_odds AS (
            SELECT DISTINCT ON (go.game_id, go.bookmaker_id)
                go.game_id,
                go.bookmaker_id,
                b.name as bookmaker_name,
                go.home_price,
                go.away_price,
                go.spread,
                go.total,
                go.over_price,
                go.under_price
            FROM nba_game_lines.game_odds go
            JOIN nba_game_lines.bookmakers b ON go.bookmaker_id = b.id
            ORDER BY go.game_id, go.bookmaker_id, go.timestamp DESC
        )
        SELECT 
            bookmaker_name,
            COUNT(DISTINCT game_id) as total_games,
            SUM(CASE WHEN home_price IS NOT NULL AND away_price IS NOT NULL THEN 1 ELSE 0 END) as moneyline_games,
            SUM(CASE WHEN spread IS NOT NULL THEN 1 ELSE 0 END) as spread_games,
            SUM(CASE WHEN total IS NOT NULL AND over_price IS NOT NULL AND under_price IS NOT NULL THEN 1 ELSE 0 END) as total_games,
            ROUND(100.0 * SUM(CASE WHEN home_price IS NOT NULL AND away_price IS NOT NULL THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT game_id), 2) as moneyline_pct,
            ROUND(100.0 * SUM(CASE WHEN spread IS NOT NULL THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT game_id), 2) as spread_pct,
            ROUND(100.0 * SUM(CASE WHEN total IS NOT NULL AND over_price IS NOT NULL AND under_price IS NOT NULL THEN 1 ELSE 0 END)::numeric / COUNT(DISTINCT game_id), 2) as total_pct
        FROM latest_odds
        GROUP BY bookmaker_name
        ORDER BY total_games DESC;
        """
    )

    with pipeline.engine.connect() as conn:
        bookmaker_stats = pd.read_sql(bookmaker_query, conn)
        print("\nData by Bookmaker:")
        print(bookmaker_stats.to_string(index=False))

    # Set date range for training data
    end_date = datetime.now()
    start_date = datetime(2020, 1, 1)  # Use all data since 2020

    print(f"\nLoading data from {start_date} to {end_date}")

    # Load and prepare data
    games_df = pipeline.load_historical_games(start_date, end_date)
    print(f"Loaded {len(games_df)} games")

    # Print data info
    print("\nData Info:")
    print(games_df.info())

    print("\nNull Value Counts:")
    print(games_df[["home_price", "away_price", "spread", "total"]].isnull().sum())

    # Calculate team statistics
    stats_df = pipeline.calculate_team_stats(games_df)
    print("Calculated team statistics")

    # Prepare features
    datasets = pipeline.prepare_features(games_df, stats_df)
    print(f"Prepared datasets:")
    for task, (X, y) in datasets.items():
        print(f"- {task}: {len(X)} samples with {len(X.columns)} features")

    # Split data
    split_datasets = pipeline.split_data(datasets)
    print("\nSplit datasets:")
    for task, (X_train, X_test, y_train, y_test) in split_datasets.items():
        print(f"- {task}: {len(X_train)} training and {len(X_test)} test samples")

    # Initialize and train model
    model = NBABaselineModel()
    print("\nTraining models...")
    train_metrics = model.train(split_datasets)

    # Evaluate model
    print("Evaluating models...")
    eval_metrics = model.evaluate(split_datasets)

    # Get feature importance
    feature_importance = model.get_feature_importance()

    # Print results
    print("\nTraining Metrics:")
    print(json.dumps(train_metrics, indent=2))

    print("\nEvaluation Metrics:")
    print(json.dumps(eval_metrics, indent=2))

    print("\nTop 5 Important Features for Each Model:")
    for model_name, importance_df in feature_importance.items():
        print(f"\n{model_name.upper()}:")
        print(importance_df.head().to_string())

    # Save metrics
    results = {
        "training_metrics": train_metrics,
        "evaluation_metrics": eval_metrics,
        "feature_importance": {
            k: v.to_dict("records") for k, v in feature_importance.items()
        },
    }

    # Create results directory if it doesn't exist
    os.makedirs("results/baseline", exist_ok=True)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"results/baseline/metrics_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to results/baseline/metrics_{timestamp}.json")


if __name__ == "__main__":
    main()
