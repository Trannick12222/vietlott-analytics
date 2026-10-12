import numpy as np
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class SimulationResult:
    total_simulations: int
    number_frequencies: Dict[int, int]
    number_probabilities: Dict[int, float]
    odd_even_distribution: Dict[str, int]
    high_low_distribution: Dict[str, int]
    sum_distribution: Dict[str, int]

class MonteCarloSimulator:
    def __init__(self, max_number: int, numbers_per_draw: int = 6):
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw

    def run_simulation(self, num_simulations: int = 100000) -> SimulationResult:
        """
        Simulate lottery draws using uniform random distribution.
        """
        rand_mat = np.random.rand(num_simulations, self.max_number)
        draws = np.argpartition(rand_mat, self.numbers_per_draw - 1, axis=1)[:, :self.numbers_per_draw] + 1
        
        unique, counts = np.unique(draws, return_counts=True)
        freq_dict = {int(k): int(v) for k, v in zip(unique, counts)}
        for i in range(1, self.max_number + 1):
            if i not in freq_dict:
                freq_dict[i] = 0
                
        prob_dict = {k: v / num_simulations for k, v in freq_dict.items()}
        
        odds = (draws % 2 != 0).sum(axis=1)
        oe_counts = np.zeros(self.numbers_per_draw + 1, dtype=int)
        u_odds, o_counts = np.unique(odds, return_counts=True)
        for u, c in zip(u_odds, o_counts):
            oe_counts[u] = c
        oe_dist = {f"{o} Odd / {self.numbers_per_draw - o} Even": int(c) for o, c in enumerate(oe_counts) if c > 0}
        
        midpoint = self.max_number / 2
        highs = (draws > midpoint).sum(axis=1)
        hl_counts = np.zeros(self.numbers_per_draw + 1, dtype=int)
        u_highs, h_counts = np.unique(highs, return_counts=True)
        for u, c in zip(u_highs, h_counts):
            hl_counts[u] = c
        hl_dist = {f"{h} High / {self.numbers_per_draw - h} Low": int(c) for h, c in enumerate(hl_counts) if c > 0}
        
        sums = draws.sum(axis=1)
        sum_unique, sum_counts = np.unique(sums, return_counts=True)
        sum_dist = {str(k): int(v) for k, v in zip(sum_unique, sum_counts)}
        
        return SimulationResult(
            total_simulations=num_simulations,
            number_frequencies=freq_dict,
            number_probabilities=prob_dict,
            odd_even_distribution=oe_dist,
            high_low_distribution=hl_dist,
            sum_distribution=sum_dist
        )


def run_simulation(n_simulations: int = 100000, game_type: str = "mega") -> Dict[str, Any]:
    """Helper function to run Monte Carlo simulation."""
    max_num = 45 if "mega" in str(game_type).lower() else 55
    simulator = MonteCarloSimulator(max_number=max_num, numbers_per_draw=6)
    res = simulator.run_simulation(n_simulations)
    return {
        "n_simulations": res.total_simulations,
        "frequencies": res.number_frequencies,
        "probabilities": res.number_probabilities,
        "odd_even_distribution": res.odd_even_distribution,
        "high_low_distribution": res.high_low_distribution,
        "sum_distribution": res.sum_distribution,
        "result_obj": res
    }

