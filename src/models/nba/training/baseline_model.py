"""
NBA Game Prediction Baseline Model

This module implements baseline models for NBA game predictions.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    mean_absolute_error,
    mean_squared_error,
    classification_report,
    precision_score,
    recall_score,
    f1_score,
    r2_score,
)


class NBABaselineModel:
    """Baseline model for NBA game predictions."""

    def __init__(self):
        """Initialize models."""
        self.models = {
            "moneyline": RandomForestClassifier(n_estimators=100, random_state=42),
            "spread": RandomForestRegressor(n_estimators=100, random_state=42),
            "total": RandomForestRegressor(n_estimators=100, random_state=42),
        }
        self.feature_names = None

    def train(
        self,
        split_datasets: Dict[
            str, Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]
        ],
    ) -> Dict[str, Dict[str, float]]:
        """Train models on the given data.

        Args:
            split_datasets: Dictionary mapping tasks to (X_train, X_test, y_train, y_test)

        Returns:
            Dictionary of training metrics for each model
        """
        metrics = {}

        for task, (X_train, _, y_train, _) in split_datasets.items():
            if task not in self.models:
                continue

            # Store feature names if not already stored
            if self.feature_names is None:
                self.feature_names = X_train.columns.tolist()

            # Train model
            self.models[task].fit(X_train, y_train)

            # Calculate training metrics
            if task == "moneyline":
                y_pred = self.models[task].predict(X_train)
                metrics[task] = {
                    "accuracy": accuracy_score(y_train, y_pred),
                    "precision": precision_score(y_train, y_pred),
                    "recall": recall_score(y_train, y_pred),
                    "f1": f1_score(y_train, y_pred),
                }
            else:
                y_pred = self.models[task].predict(X_train)
                metrics[task] = {
                    "mse": mean_squared_error(y_train, y_pred),
                    "mae": mean_absolute_error(y_train, y_pred),
                    "r2": r2_score(y_train, y_pred),
                }

        return metrics

    def evaluate(
        self,
        split_datasets: Dict[
            str, Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]
        ],
    ) -> Dict[str, Dict[str, float]]:
        """Evaluate models on test data.

        Args:
            split_datasets: Dictionary mapping tasks to (X_train, X_test, y_train, y_test)

        Returns:
            Dictionary of evaluation metrics for each model
        """
        metrics = {}

        for task, (_, X_test, _, y_test) in split_datasets.items():
            if task not in self.models:
                continue

            # Make predictions
            y_pred = self.models[task].predict(X_test)

            # Calculate metrics
            if task == "moneyline":
                metrics[task] = {
                    "accuracy": accuracy_score(y_test, y_pred),
                    "precision": precision_score(y_test, y_pred),
                    "recall": recall_score(y_test, y_pred),
                    "f1": f1_score(y_test, y_pred),
                }
            else:
                metrics[task] = {
                    "mse": mean_squared_error(y_test, y_pred),
                    "mae": mean_absolute_error(y_test, y_pred),
                    "r2": r2_score(y_test, y_pred),
                }

        return metrics

    def get_feature_importance(self) -> Dict[str, pd.DataFrame]:
        """Get feature importance for each model.

        Returns:
            Dictionary mapping model names to feature importance DataFrames
        """
        importance = {}

        for task, model in self.models.items():
            if not hasattr(model, "feature_importances_"):
                continue

            importance[task] = pd.DataFrame(
                {
                    "feature": self.feature_names,
                    "importance": model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)

        return importance
