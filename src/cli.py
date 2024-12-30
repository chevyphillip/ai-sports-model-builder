"""Command-line interface for the sports model."""

import click
from src.core.logger import logger
from src.core.config import DB_NAME


@click.group()
def cli():
    """AI Sports Model Builder CLI."""
    pass


@cli.command()
def init():
    """Initialize the database and required resources."""
    from src.core.database import init_db

    logger.info(f"Initializing database: {DB_NAME}")
    init_db()
    logger.info("Database initialization complete")


@cli.command()
@click.option("--sport", type=click.Choice(["NBA", "NFL", "NHL"]), required=True)
def fetch_data(sport):
    """Fetch data for a specific sport."""
    from src.services.data_collection.odds_service import fetch_odds_data

    logger.info(f"Fetching data for {sport}")
    fetch_odds_data(sport)


@cli.command()
@click.option("--sport", type=click.Choice(["NBA", "NFL", "NHL"]), required=True)
@click.option("--model-type", type=click.Choice(["basic", "advanced"]), default="basic")
def train(sport, model_type):
    """Train models for a specific sport."""
    from src.services.prediction.training import train_model

    logger.info(f"Training {model_type} model for {sport}")
    train_model(sport, model_type)


@cli.command()
@click.option("--sport", type=click.Choice(["NBA", "NFL", "NHL"]), required=True)
def predict(sport):
    """Generate predictions for upcoming games."""
    from src.services.prediction.predictor import generate_predictions

    logger.info(f"Generating predictions for {sport}")
    generate_predictions(sport)


def main():
    """Main entry point for the CLI."""
    cli()
