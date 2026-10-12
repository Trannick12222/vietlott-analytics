from dataclasses import dataclass
from typing import List, Dict, Any
from .scoring import EnsembleScoringEngine, NumberScore
from .combination import CombinationGenerator, Combination
from ..simulation.monte_carlo import MonteCarloSimulator

@dataclass
class PredictionResult:
    ranked_numbers: List[NumberScore]
    combinations: List[Combination]
    mathematical_probability: float
    disclaimer: str = "DISCLAIMER: Lottery draws are purely random. The 'Model Score' is an analytical metric, not a mathematical probability of winning. Always play responsibly."

class Predictor:
    def __init__(self, max_number: int, numbers_per_draw: int = 6):
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.scoring_engine = EnsembleScoringEngine(max_number)
        self.combo_generator = CombinationGenerator(max_number, numbers_per_draw)
        self.simulator = MonteCarloSimulator(max_number, numbers_per_draw)
        
    def predict(self, statistical_raw_scores: Dict[str, Dict[int, float]], threshold: float = 50.0) -> PredictionResult:
        # Run MC simulation to get MC scores
        mc_result = self.simulator.run_simulation(100000)
        statistical_raw_scores['monte_carlo'] = mc_result.number_probabilities
        
        # Calculate ensemble scores
        scores = self.scoring_engine.calculate_ensemble_scores(statistical_raw_scores)
        
        # Rank and filter
        ranked = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
        filtered = [s for s in ranked if s.final_model_score >= threshold]
        
        # Generate combinations
        combos = self.combo_generator.generate(scores)
        
        # Mathematical probability baseline
        # (Simplified combinations logic)
        import math
        total_combinations = math.comb(self.max_number, self.numbers_per_draw)
        prob = 1.0 / total_combinations
        
        return PredictionResult(
            ranked_numbers=filtered if filtered else ranked,
            combinations=combos,
            mathematical_probability=prob
        )
