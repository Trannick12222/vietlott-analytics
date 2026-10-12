from dataclasses import dataclass
from typing import List, Dict, Any
from .frequency import analyze_frequency, analyze_moving_window
from .recency import analyze_recency
from .distribution import analyze_distribution
from .consecutive import analyze_consecutive
from .correlation import analyze_correlation
from .bayesian import analyze_bayesian
from .probability import analyze_probability
from .regime import analyze_regime_and_extremes

@dataclass
class StatisticalResult:
    lottery_type: str
    total_draws: int
    frequency: Dict[str, Any]
    moving_window: Dict[int, Dict[int, List[int]]]
    recency: Dict[str, Any]
    distribution: Dict[str, Any]
    consecutive: Dict[str, Any]
    correlation: Dict[str, Any]
    bayesian: Dict[str, Any]
    probability: Dict[str, Any]
    regime: Dict[str, Any] = None

def analyze_all(draws: List[List[int]], lottery_type: str = "mega", decay_factor: float = 0.05) -> StatisticalResult:
    """
    Orchestrate all statistical analysis modules.
    
    Args:
        draws: List of draw data (list of lists of integers)
        lottery_type: "mega" or "power"
        decay_factor: Decay factor for weighted frequency calculation
        
    Returns:
        StatisticalResult containing all analysis outputs
    """
    return StatisticalResult(
        lottery_type=lottery_type,
        total_draws=len(draws),
        frequency=analyze_frequency(draws, lottery_type, decay_factor),
        moving_window=analyze_moving_window(draws, [5, 10, 20, 50, 100], lottery_type),
        recency=analyze_recency(draws, lottery_type),
        distribution=analyze_distribution(draws, lottery_type),
        consecutive=analyze_consecutive(draws, lottery_type),
        correlation=analyze_correlation(draws, lottery_type),
        bayesian=analyze_bayesian(draws, lottery_type),
        probability=analyze_probability(draws, lottery_type),
        regime=analyze_regime_and_extremes(draws, lottery_type)
    )
