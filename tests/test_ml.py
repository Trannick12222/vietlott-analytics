import pytest
from src.ml.models import LotteryMLModel

def test_ml_skipped_on_small_data():
    ml = LotteryMLModel(min_draws=50)
    # 10 draws
    res = ml.train_and_predict([[1, 2, 3, 4, 5, 6]] * 10)
    assert res["status"] == "skipped"
    assert "Statistical model > ML model" in res["reason"]

def test_ml_warn_on_medium_data():
    ml = LotteryMLModel(min_draws=50)
    # 30 draws
    res = ml.train_and_predict([[1, 2, 3, 4, 5, 6]] * 30)
    assert res["status"] in ["skipped_or_warn", "skipped"]
    assert "ML predictions may be unreliable" in res["reason"]

def test_ml_runs_on_sufficient_data():
    ml = LotteryMLModel(min_draws=50)
    # 60 draws
    res = ml.train_and_predict([[1, 2, 3, 4, 5, 6]] * 60)
    assert res["status"] == "success"
    assert "Logistic Regression" in res["models_trained"]
    assert "disclaimer" in res
