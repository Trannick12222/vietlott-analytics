import pytest
from src.prediction.scoring import EnsembleScoringEngine, ScoreWeights, NumberScore

def test_ensemble_scoring_engine_initialization():
    engine = EnsembleScoringEngine(max_number=45)
    assert engine.max_number == 45
    assert engine.weights is not None

def test_score_weights_normalization():
    weights = ScoreWeights(frequency=2.0, weighted_frequency=2.0, recency=2.0, bayesian=2.0,
                           co_occurrence=0.0, range_dist=0.0, odd_even_balance=0.0, monte_carlo=0.0)
    weights.normalize()
    assert abs(sum([weights.frequency, weights.weighted_frequency, weights.recency, weights.bayesian]) - 1.0) < 1e-5

def test_score_normalization():
    engine = EnsembleScoringEngine(max_number=45)
    scores = {1: 0.0, 2: 50.0, 3: 100.0}
    normalized = engine._normalize_scores(scores)
    assert normalized[1] == 0.0
    assert normalized[3] == 100.0
    assert normalized[2] == 50.0

def test_ensemble_score_calculation():
    engine = EnsembleScoringEngine(max_number=45)
    raw_scores = {
        "frequency": {1: 100.0, 2: 0.0},
        "weighted_frequency": {1: 100.0, 2: 0.0},
        "recency": {1: 100.0, 2: 0.0},
        "bayesian": {1: 100.0, 2: 0.0}
    }
    results = engine.calculate_ensemble_scores(raw_scores)
    assert 1 in results
    assert 2 in results
    assert isinstance(results[1], NumberScore)
    assert results[1].final_model_score > results[2].final_model_score

def test_confidence_levels():
    engine = EnsembleScoringEngine(max_number=45)
    # When a number scores highest across all 3 key components, its normalized scores are all 100.0 (variance = 0)
    raw_scores = {
        "weighted_frequency": {1: 100.0, 2: 10.0},
        "bayesian": {1: 100.0, 2: 10.0},
        "recency": {1: 100.0, 2: 10.0}
    }
    results = engine.calculate_ensemble_scores(raw_scores)
    assert results[1].confidence_level == "High"

def test_with_empty_scores():
    engine = EnsembleScoringEngine(max_number=45)
    results = engine.calculate_ensemble_scores({})
    assert len(results) == 45
    assert all(s.final_model_score == 0.0 for s in results.values())
