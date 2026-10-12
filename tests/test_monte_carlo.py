import pytest
from src.simulation.monte_carlo import run_simulation

def test_simulation_runs_without_error():
    results = run_simulation(n_simulations=1000, game_type="mega")
    assert results is not None

def test_number_probabilities_are_reasonable():
    results = run_simulation(n_simulations=10000, game_type="mega")
    probabilities = results.get("probabilities", {})
    assert len(probabilities) == 45
    for num, prob in probabilities.items():
        assert 0.0 <= prob <= 1.0

def test_sum_is_close_to_expected():
    results = run_simulation(n_simulations=10000, game_type="mega")
    # Expected sum of probabilities across all numbers for 6 draws should be roughly 6
    total_prob = sum(results.get("probabilities", {}).values())
    assert 5.0 <= total_prob <= 7.0

def test_all_numbers_appear_at_least_once():
    results = run_simulation(n_simulations=10000, game_type="mega")
    frequencies = results.get("frequencies", {})
    assert all(freq > 0 for freq in frequencies.values())

def test_configurable_simulation_count():
    results_100 = run_simulation(n_simulations=100, game_type="mega")
    assert results_100["n_simulations"] == 100
