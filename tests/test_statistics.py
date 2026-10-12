import pytest
from src.statistics.frequency import analyze_frequency
from src.statistics.recency import analyze_recency
from src.statistics.distribution import analyze_distribution
from src.statistics.consecutive import analyze_consecutive
from src.statistics.bayesian import analyze_bayesian
from src.statistics.probability import analyze_probability
from src.statistics.engine import analyze_all, StatisticalResult

def test_frequency_analysis(sample_mega_draws):
    freq = analyze_frequency(sample_mega_draws, lottery_type="mega")
    assert isinstance(freq, dict)
    assert "counts" in freq
    assert "frequency_pct" in freq
    assert len(freq["counts"]) == 45

def test_recency_analysis(sample_mega_draws):
    recency = analyze_recency(sample_mega_draws, lottery_type="mega")
    assert isinstance(recency, dict)
    assert "gaps" in recency
    assert "hot" in recency
    assert "cold" in recency
    assert len(recency["gaps"]) == 45

def test_distribution_analysis(sample_mega_draws):
    dist = analyze_distribution(sample_mega_draws, lottery_type="mega")
    assert isinstance(dist, dict)
    assert "odd_even_overall" in dist
    assert "high_low_overall" in dist
    assert "bucket_counts_overall" in dist

def test_consecutive_analysis(sample_mega_draws):
    cons = analyze_consecutive(sample_mega_draws, lottery_type="mega")
    assert isinstance(cons, dict)
    assert "pairs_per_draw" in cons or "pairs_frequency" in cons

def test_bayesian_analysis(sample_mega_draws):
    bayes = analyze_bayesian(sample_mega_draws, lottery_type="mega")
    assert isinstance(bayes, dict)
    # Each number has a posterior_mean > 0
    assert 1 in bayes
    assert all(bayes[n]["posterior_mean"] > 0 for n in bayes)

def test_probability_calculations(sample_mega_draws):
    prob = analyze_probability(sample_mega_draws, lottery_type="mega")
    assert isinstance(prob, dict)
    assert "baseline_prob" in prob
    assert abs(prob["baseline_prob"] - (6 / 45)) < 1e-4

def test_analyze_all(sample_mega_draws):
    result = analyze_all(sample_mega_draws, lottery_type="mega")
    assert isinstance(result, StatisticalResult)
    assert result.total_draws == len(sample_mega_draws)
    assert "counts" in result.frequency
    assert 1 in result.bayesian

def test_empty_draws_handling():
    result = analyze_all([], lottery_type="mega")
    assert result.total_draws == 0
    assert result.frequency["counts"] == {}

def test_single_draw_handling():
    result = analyze_all([[1, 2, 3, 4, 5, 6]], lottery_type="mega")
    assert result.total_draws == 1
    assert result.frequency["counts"][1] == 1

def test_regime_and_extremes_analysis(sample_mega_draws, sample_power_draws):
    from src.statistics.regime import analyze_regime_and_extremes
    
    # Test Mega
    res_mega = analyze_regime_and_extremes(sample_mega_draws, lottery_type="mega")
    assert "order_statistics" in res_mega
    assert "regime_analysis" in res_mega
    assert "mean_reversion" in res_mega
    assert res_mega["order_statistics"]["theoretical_max"] == 39.43
    assert res_mega["order_statistics"]["theoretical_min"] == 6.57
    assert "next_draw_forecast" in res_mega["regime_analysis"]
    assert res_mega["regime_analysis"]["next_draw_forecast"]["predicted_regime"] in ["LOW", "STD", "HIGH"]

    # Test Power
    res_power = analyze_regime_and_extremes(sample_power_draws, lottery_type="power")
    assert res_power["order_statistics"]["theoretical_max"] == 48.0
    assert res_power["order_statistics"]["theoretical_min"] == 8.0
    assert "probabilities" in res_power["regime_analysis"]["next_draw_forecast"]
    assert "reversion_status" in res_power["mean_reversion"]

