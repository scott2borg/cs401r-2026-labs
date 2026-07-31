"""
NorthStar Retail — Model Evaluation Tests
CS 401R Lab 4 Starter Kit

These tests verify that the churn model meets production quality gates before
it can be promoted through the Model Registry. They run in the CodeBuild
pre_build phase against the latest trained model artifact.

The key design decision here: we test the MODEL CONTRACT, not the model's
internal implementation. These tests would catch:
  - A model that always predicts "not churned" (high accuracy, useless)
  - A model that performs well on aggregate but fails on a key customer segment
  - A model artifact that can't load or can't produce valid probability scores
  - Prediction drift between model versions

Run locally:
    # First train a model or download from S3:
    # aws s3 cp s3://your-bucket/artifacts/models/latest/model.xgb ./test_model.xgb
    pytest tests/test_model.py -v --model-path ./test_model.xgb
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# ── CLI Option ─────────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption(
        "--model-path", action="store", default=None,
        help="Path to trained XGBoost model (.xgb file)"
    )


@pytest.fixture(scope="session")
def model_path(request):
    path = request.config.getoption("--model-path")
    if path is None:
        path = os.environ.get("MODEL_PATH", "./model/model.xgb")
    return path


# ── Fixtures ──────────────────────────────────────────────────────────────────

# These are the model's input features. They must match the FEATURE_COLUMNS in
# churn_training_skeleton.py and every one must exist in the Lab 2 Feature Group.
# churn_label is the target and churn_risk_score is the baseline - neither is an input.
FEATURE_COLUMNS = [
    "days_since_last_purchase",
    "customer_tenure_days",
    "purchase_frequency_30d",
    "purchase_frequency_90d",
    "purchase_frequency_180d",
    "avg_order_value",
    "total_spend_90d",
    "total_lifetime_value",
    "avg_basket_size_6m",
    "category_diversity_score",
    "online_to_store_ratio",
]


@pytest.fixture(scope="module")
def loaded_model(model_path):
    """Load the trained model. Skip if file doesn't exist."""
    if not XGBOOST_AVAILABLE:
        pytest.skip("xgboost not installed")
    if not Path(model_path).exists():
        pytest.skip(f"Model file not found at {model_path}. Train a model first.")
    model = xgb.Booster()
    model.load_model(model_path)
    return model


@pytest.fixture(scope="module")
def model_metadata(model_path):
    """Load model metadata if it exists alongside the model."""
    meta_path = Path(model_path).parent / "model_metadata.json"
    if meta_path.exists():
        with open(meta_path) as f:
            return json.load(f)
    return {}


@pytest.fixture
def synthetic_churn_batch():
    """
    Synthetic batch of 200 customers with known expected behavior.
    Group A (100): Clear churners — high recency, low frequency, low spend
    Group B (100): Clear retainers — low recency, high frequency, high spend
    """
    np.random.seed(42)
    n = 100

    # Group A: high churn risk
    churners = pd.DataFrame({
        "days_since_last_purchase":     np.random.randint(90, 200, n),
        "purchase_frequency_90d":       np.random.randint(0, 2, n),
        "purchase_frequency_180d":      np.random.randint(0, 3, n),
        "avg_basket_size_6m":           np.random.uniform(20, 60, n),
        "total_spend_90d":              np.random.uniform(0, 50, n),
        "category_diversity_score":     np.random.uniform(0, 0.3, n),
        "online_to_store_ratio":        np.random.uniform(0, 0.2, n),
        "customer_tenure_days":         np.random.randint(30, 365, n),
        "purchase_frequency_30d":       np.zeros(n),
        "avg_order_value":              np.random.uniform(20, 60, n),
        "total_lifetime_value":         np.random.uniform(50, 400, n),
        "true_label":                   np.ones(n),  # Expected: high churn score
    })

    # Group B: low churn risk
    retainers = pd.DataFrame({
        "days_since_last_purchase":     np.random.randint(1, 15, n),
        "purchase_frequency_90d":       np.random.randint(6, 20, n),
        "purchase_frequency_180d":      np.random.randint(10, 35, n),
        "avg_basket_size_6m":           np.random.uniform(120, 400, n),
        "total_spend_90d":              np.random.uniform(400, 2000, n),
        "category_diversity_score":     np.random.uniform(0.5, 1.0, n),
        "online_to_store_ratio":        np.random.uniform(0.4, 0.8, n),
        "customer_tenure_days":         np.random.randint(300, 420, n),
        "purchase_frequency_30d":       np.random.randint(2, 8, n),
        "avg_order_value":              np.random.uniform(120, 400, n),
        "total_lifetime_value":         np.random.uniform(1500, 9000, n),
        "true_label":                   np.zeros(n),  # Expected: low churn score
    })

    return pd.concat([churners, retainers], ignore_index=True)


# ── Model Loading Tests ────────────────────────────────────────────────────────

class TestModelLoading:

    def test_model_loads_successfully(self, loaded_model):
        assert loaded_model is not None

    def test_model_has_expected_feature_count(self, loaded_model):
        """Model should have been trained on exactly 12 features."""
        n_features = loaded_model.num_features()
        assert n_features == len(FEATURE_COLUMNS), (
            f"Model has {n_features} features, expected {len(FEATURE_COLUMNS)}. "
            f"Feature columns may have changed."
        )

    def test_model_metadata_exists(self, model_metadata):
        """model_metadata.json should be saved alongside the model."""
        assert model_metadata, (
            "model_metadata.json not found. The training script must save metadata alongside the model artifact."
        )

    def test_model_metadata_has_evaluation_metrics(self, model_metadata):
        if not model_metadata:
            pytest.skip("No metadata available")
        assert "evaluation_metrics" in model_metadata, (
            "Metadata must include evaluation_metrics from training"
        )

    def test_metadata_records_feature_list(self, model_metadata):
        if not model_metadata:
            pytest.skip("No metadata available")
        recorded_features = model_metadata.get("feature_columns", [])
        assert recorded_features == FEATURE_COLUMNS, (
            f"Metadata feature list doesn't match expected. "
            f"Got {recorded_features}, expected {FEATURE_COLUMNS}"
        )


# ── Prediction Output Tests ────────────────────────────────────────────────────

class TestPredictionOutput:

    def test_predictions_are_probabilities(self, loaded_model, synthetic_churn_batch):
        """Output must be probabilities in [0, 1] — not class labels or log-odds."""
        features = synthetic_churn_batch[FEATURE_COLUMNS]
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        predictions = loaded_model.predict(dmatrix)

        assert predictions.min() >= 0.0, f"Predictions below 0: {predictions.min():.4f}"
        assert predictions.max() <= 1.0, f"Predictions above 1: {predictions.max():.4f}"

    def test_predictions_have_no_nans(self, loaded_model, synthetic_churn_batch):
        features = synthetic_churn_batch[FEATURE_COLUMNS]
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        predictions = loaded_model.predict(dmatrix)
        nan_count = np.isnan(predictions).sum()
        assert nan_count == 0, f"{nan_count} NaN predictions — possible missing value issue"

    def test_predictions_use_full_probability_range(self, loaded_model, synthetic_churn_batch):
        """The model should output scores spread across [0.05, 0.95] — not all clustered near 0.5."""
        features = synthetic_churn_batch[FEATURE_COLUMNS]
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        predictions = loaded_model.predict(dmatrix)
        spread = predictions.max() - predictions.min()
        assert spread > 0.4, (
            f"Predictions are too tightly clustered (range: {spread:.2f}). "
            f"Model may be underfitting or always predicting the mean."
        )

    def test_single_sample_inference(self, loaded_model):
        """Model must handle a single-row input without errors."""
        single_sample = pd.DataFrame([{f: 0.0 for f in FEATURE_COLUMNS}])
        # Set some realistic values
        single_sample["days_since_last_purchase"] = 45
        single_sample["purchase_frequency_90d"] = 2
        single_sample["customer_tenure_days"] = 730

        dmatrix = xgb.DMatrix(single_sample, feature_names=FEATURE_COLUMNS)
        pred = loaded_model.predict(dmatrix)
        assert len(pred) == 1
        assert 0 <= pred[0] <= 1


# ── Discrimination Quality Tests ───────────────────────────────────────────────

class TestModelDiscrimination:

    def test_churners_score_higher_than_retainers(self, loaded_model, synthetic_churn_batch):
        """
        The model should assign higher churn scores to the synthetic churner group
        than to the retainer group. This is the most basic sanity check.
        """
        features = synthetic_churn_batch[FEATURE_COLUMNS]
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        predictions = loaded_model.predict(dmatrix)

        churner_mask = synthetic_churn_batch["true_label"] == 1
        retainer_mask = synthetic_churn_batch["true_label"] == 0

        avg_churn_score = predictions[churner_mask].mean()
        avg_retain_score = predictions[retainer_mask].mean()

        assert avg_churn_score > avg_retain_score + 0.15, (
            f"Churner avg score ({avg_churn_score:.3f}) should be significantly higher than "
            f"retainer avg score ({avg_retain_score:.3f}). "
            f"Gap: {avg_churn_score - avg_retain_score:.3f} — expected > 0.15"
        )

    def test_auc_roc_on_synthetic_data(self, loaded_model, synthetic_churn_batch):
        """AUC-ROC on synthetic data with clear signal should be > 0.80."""
        try:
            from sklearn.metrics import roc_auc_score
        except ImportError:
            pytest.skip("scikit-learn not installed")

        features = synthetic_churn_batch[FEATURE_COLUMNS]
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        predictions = loaded_model.predict(dmatrix)
        labels = synthetic_churn_batch["true_label"].values

        auc = roc_auc_score(labels, predictions)
        assert auc > 0.80, (
            f"AUC-ROC on synthetic data is {auc:.4f} — expected > 0.80 on clearly labeled data. "
            f"Check that feature engineering matches what the model was trained on."
        )


# ── Sensitivity / Robustness Tests ─────────────────────────────────────────────

class TestModelRobustness:

    def test_model_handles_missing_values(self, loaded_model):
        """
        XGBoost handles NaN natively. Verify the model doesn't crash on null features.
        In production, Feature Store may return NaN for customers with no clickstream.
        """
        features_with_nulls = pd.DataFrame([{f: np.nan for f in FEATURE_COLUMNS}])
        features_with_nulls["days_since_last_purchase"] = 30  # at least some real values
        dmatrix = xgb.DMatrix(features_with_nulls, feature_names=FEATURE_COLUMNS)
        pred = loaded_model.predict(dmatrix)
        assert len(pred) == 1
        assert not np.isnan(pred[0]), "Model predicted NaN on null-feature input"

    def test_model_monotone_on_recency(self, loaded_model):
        """
        Increasing days_since_last_purchase (more dormant) should increase churn probability.
        This tests that the model learned the correct direction for the recency feature.

        TODO: This is a monotonicity test — a form of model behavior testing that
        goes beyond aggregate metrics. Implement it.
        """
        recency_values = [5, 30, 60, 90, 150, 200]
        scores = []

        for days in recency_values:
            features = pd.DataFrame([{
                "days_since_last_purchase": days,
                "purchase_frequency_90d": 3,
                "purchase_frequency_180d": 6,
                "avg_basket_size_6m": 85.0,
                "total_spend_90d": 200.0,
                "category_diversity_score": 0.5,
                "online_to_store_ratio": 0.4,
                "avg_order_value": 120.0,
                "total_lifetime_value": 2400.0,
                "customer_tenure_days": 1000,
                "purchase_frequency_30d": 2,
            }])
            dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
            scores.append(float(loaded_model.predict(dmatrix)[0]))

        # Scores should be generally increasing (more dormant = higher churn risk)
        # Allow some non-monotonicity but the overall trend must be upward
        increasing_pairs = sum(scores[i] < scores[i+1] for i in range(len(scores)-1))
        assert increasing_pairs >= 4, (
            f"Model is not monotone on recency. Scores: {[f'{s:.3f}' for s in scores]}. "
            f"Only {increasing_pairs}/5 pairs are increasing — expected ≥ 4."
        )

    def test_prediction_stability_across_calls(self, loaded_model):
        """Same input must produce identical output on repeated calls (deterministic)."""
        features = pd.DataFrame([{
            "days_since_last_purchase": 45, "purchase_frequency_90d": 3,
            "purchase_frequency_180d": 6, "avg_basket_size_6m": 85.0,
            "total_spend_90d": 200.0, "category_diversity_score": 0.5,
            "online_to_store_ratio": 0.4, "avg_order_value": 120.0,
            "total_lifetime_value": 2400.0, "customer_tenure_days": 365,
            "purchase_frequency_30d": 2,
        }])
        dmatrix = xgb.DMatrix(features, feature_names=FEATURE_COLUMNS)
        pred1 = loaded_model.predict(dmatrix)[0]
        pred2 = loaded_model.predict(dmatrix)[0]
        assert pred1 == pred2, f"Model is non-deterministic: {pred1} != {pred2}"


# ── Stored Metrics Quality Gate ────────────────────────────────────────────────

class TestStoredMetricsGate:
    """
    Reads the evaluation_metrics.json saved by the training script and
    verifies the model passed all required thresholds.
    These tests are the definitive quality gate in the CI pipeline.
    """

    REQUIRED_METRICS = {
        "auc_roc": 0.72,
        "precision_top10": 0.40,
        "recall_top10": 0.35,
        "auc_vs_baseline": 0.05,
    }

    @pytest.fixture(scope="class")
    def eval_metrics(self):
        metrics_path = os.environ.get("EVAL_METRICS_PATH", "/tmp/eval_metrics.json")
        if not Path(metrics_path).exists():
            pytest.skip(f"Evaluation metrics not found at {metrics_path}.")
        with open(metrics_path) as f:
            return json.load(f)

    def test_auc_roc_meets_threshold(self, eval_metrics):
        auc = eval_metrics.get("auc_roc", 0)
        assert auc >= self.REQUIRED_METRICS["auc_roc"], (
            f"AUC-ROC {auc:.4f} < required {self.REQUIRED_METRICS['auc_roc']}"
        )

    def test_precision_top10_meets_threshold(self, eval_metrics):
        p = eval_metrics.get("precision_top10", 0)
        assert p >= self.REQUIRED_METRICS["precision_top10"], (
            f"Precision@Top10 {p:.4f} < required {self.REQUIRED_METRICS['precision_top10']}"
        )

    def test_recall_top10_meets_threshold(self, eval_metrics):
        r = eval_metrics.get("recall_top10", 0)
        assert r >= self.REQUIRED_METRICS["recall_top10"], (
            f"Recall@Top10 {r:.4f} < required {self.REQUIRED_METRICS['recall_top10']}"
        )

    def test_model_beats_baseline(self, eval_metrics):
        delta = eval_metrics.get("auc_vs_baseline", 0)
        assert delta >= self.REQUIRED_METRICS["auc_vs_baseline"], (
            f"AUC vs baseline {delta:.4f} < required {self.REQUIRED_METRICS['auc_vs_baseline']}. "
            f"Model barely outperforms predicting the mean churn rate."
        )

    def test_positive_rate_is_realistic(self, eval_metrics):
        """The validation set churn rate should be near the expected 15%."""
        rate = eval_metrics.get("positive_rate_val", -1)
        if rate < 0:
            pytest.skip("positive_rate_val not in metrics")
        assert 0.08 <= rate <= 0.25, (
            f"Validation churn rate {rate:.1%} outside expected range [8%, 25%]. "
            f"Check that your validation split is stratified."
        )
