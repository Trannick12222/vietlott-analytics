import scipy.stats as stats
from typing import List, Dict, Any

def analyze_probability(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform mathematical probability calculations and goodness-of-fit testing.
    """
    max_num = 45 if lottery_type.lower() == "mega" else 55
    baseline_prob = 6 / max_num
    
    if not draws:
        return {
            "baseline_prob": baseline_prob,
            "expected_appearances": 0.0
        }

    total_draws = len(draws)
    expected_appearances = total_draws * baseline_prob
    
    # Count observed frequencies
    counts = {i: 0 for i in range(1, max_num + 1)}
    for draw in draws:
        for num in draw:
            if 1 <= num <= max_num:
                counts[num] += 1
                
    observed = [counts[i] for i in range(1, max_num + 1)]
    expected = [expected_appearances] * max_num
    
    # Chi-square test for uniformity
    # Null hypothesis: numbers are drawn uniformly with probability 6/max_num
    chi2_stat, p_value = stats.chisquare(f_obs=observed, f_exp=expected)
    
    # Binomial probability of exactly k appearances in N draws
    # Let's calculate for a typical number (say, k=expected)
    k_example = int(expected_appearances)
    prob_exactly_k = stats.binom.pmf(k_example, total_draws, baseline_prob)
    
    return {
        "baseline_prob": float(baseline_prob),
        "expected_appearances": float(expected_appearances),
        "chi_square_stat": float(chi2_stat),
        "p_value": float(p_value),
        "is_uniform": bool(p_value > 0.05),  # If p > 0.05, we fail to reject null hypothesis (likely uniform)
        "example_binomial_prob": {
            "k": int(k_example),
            "prob": float(prob_exactly_k)
        }
    }
