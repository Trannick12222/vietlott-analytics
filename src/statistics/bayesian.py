import scipy.stats as stats
from typing import List, Dict, Any

def analyze_bayesian(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform Bayesian analysis using a Beta-Binomial model.
    Prior: Beta(1,1) uniform prior
    """
    max_num = 45 if lottery_type.lower() == "mega" else 55
    if not draws:
        return {}

    total_draws = len(draws)
    
    # Count appearances
    counts = {i: 0 for i in range(1, max_num + 1)}
    for draw in draws:
        for num in draw:
            if 1 <= num <= max_num:
                counts[num] += 1
                
    # Beta(alpha, beta) prior where alpha=1, beta=1
    prior_alpha = 1
    prior_beta = 1
    
    results = {}
    
    for num in range(1, max_num + 1):
        successes = counts[num]
        failures = total_draws - successes
        
        # Posterior Beta parameters
        post_alpha = prior_alpha + successes
        post_beta = prior_beta + failures
        
        # Posterior mean (expected probability)
        posterior_mean = float(post_alpha / (post_alpha + post_beta))
        
        # 95% Credible Interval
        ci_lower = float(stats.beta.ppf(0.025, post_alpha, post_beta))
        ci_upper = float(stats.beta.ppf(0.975, post_alpha, post_beta))
        
        results[num] = {
            "appearances": int(successes),
            "posterior_mean": posterior_mean,
            "credible_interval_95": [ci_lower, ci_upper]
        }
        
    return results
