import numpy as np
import pandas as pd
import random
import math
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from src.statistics.engine import analyze_all
from src.prediction.scoring import EnsembleScoringEngine

@dataclass
class BacktestResult:
    total_evaluations: int
    hit_rate: float
    avg_matched: float
    top_1_accuracy: float
    top_5_accuracy: float
    top_10_accuracy: float
    precision: float
    recall: float
    brier_score: float
    random_baseline: Dict[str, float]
    freq_baseline: Dict[str, float]
    weighted_freq_baseline: Dict[str, float]
    better_than_random: bool

class Backtester:
    def __init__(self, lottery_type: str = "mega645"):
        self.lottery_type = lottery_type
        self.max_num = 45 if lottery_type == "mega645" else 55
        self.num_picks = 6
        self.scoring_engine = EnsembleScoringEngine(lottery_type)
        
    def _get_draw_numbers(self, draw: Dict[str, Any]) -> List[int]:
        """Extract main numbers from a draw."""
        return [draw[f'num{i}'] for i in range(1, 7)]

    def _random_baseline(self, actual: List[int], n_sims: int = 1000) -> Dict[str, float]:
        """Run random baseline simulations."""
        matches = []
        for _ in range(n_sims):
            pred = random.sample(range(1, self.max_num + 1), self.num_picks)
            matches.append(len(set(pred) & set(actual)))
        
        return {
            "avg_matched": float(np.mean(matches)),
            "hit_rate": float(sum(1 for m in matches if m > 0) / n_sims)
        }

    def _get_frequent_numbers(self, stats: Dict[str, Any], top_n: int = 6) -> List[int]:
        """Get most frequent numbers from stats."""
        freq_df = stats.get('frequency', pd.DataFrame())
        if freq_df.empty:
            return random.sample(range(1, self.max_num + 1), top_n)
        
        sorted_freq = freq_df.sort_values(by='frequency', ascending=False)
        return sorted_freq['number'].head(top_n).tolist()

    def _get_weighted_frequent_numbers(self, stats: Dict[str, Any], top_n: int = 6) -> List[int]:
        """Get weighted frequent numbers from stats."""
        freq_df = stats.get('frequency', pd.DataFrame())
        if freq_df.empty or 'weighted_frequency' not in freq_df.columns:
            return self._get_frequent_numbers(stats, top_n)
            
        sorted_freq = freq_df.sort_values(by='weighted_frequency', ascending=False)
        return sorted_freq['number'].head(top_n).tolist()

    def run(self, draws: List[Dict[str, Any]], window_size: int = 50) -> BacktestResult:
        """
        Run backtesting simulation using rolling windows.
        """
        if len(draws) <= window_size:
            raise ValueError(f"Number of draws ({len(draws)}) must be greater than window size ({window_size})")

        evaluations = 0
        hits = 0
        total_matched = 0
        top_1_hits = 0
        top_5_hits = 0
        top_10_hits = 0
        precisions = []
        recalls = []
        brier_scores = []
        
        random_baselines = []
        freq_matches = []
        weighted_freq_matches = []

        sorted_draws = sorted(draws, key=lambda x: x.get('draw_date', x.get('draw_number', 0)))

        for i in range(len(sorted_draws) - window_size):
            window_draws = sorted_draws[i:i + window_size]
            actual_next_draw = sorted_draws[i + window_size]
            actual_numbers = set(self._get_draw_numbers(actual_next_draw))

            stats = analyze_all(window_draws, self.lottery_type)
            
            predictions = self.scoring_engine.score_numbers(stats)
            if not predictions:
                continue

            sorted_preds = sorted(predictions, key=lambda x: x.score, reverse=True)
            top_preds = [p.number for p in sorted_preds]
            
            top_6 = set(top_preds[:6])
            top_1 = set(top_preds[:1])
            top_5 = set(top_preds[:5])
            top_10 = set(top_preds[:10])

            matched = len(top_6 & actual_numbers)
            total_matched += matched
            if matched > 0:
                hits += 1
                
            if len(top_1 & actual_numbers) > 0: top_1_hits += 1
            if len(top_5 & actual_numbers) > 0: top_5_hits += 1
            if len(top_10 & actual_numbers) > 0: top_10_hits += 1

            precisions.append(matched / 6.0)
            recalls.append(matched / 6.0)

            mse = 0
            for p in sorted_preds:
                actual_val = 1.0 if p.number in actual_numbers else 0.0
                prob = min(max(p.score, 0.0), 1.0) 
                mse += (prob - actual_val) ** 2
            brier_scores.append(mse / self.max_num)
            
            random_baselines.append(self._random_baseline(list(actual_numbers)))
            
            freq_pred = set(self._get_frequent_numbers(stats))
            freq_matches.append(len(freq_pred & actual_numbers))
            
            wfreq_pred = set(self._get_weighted_frequent_numbers(stats))
            weighted_freq_matches.append(len(wfreq_pred & actual_numbers))

            evaluations += 1

        if evaluations == 0:
            raise ValueError("No evaluations could be performed.")

        avg_random_matched = np.mean([b['avg_matched'] for b in random_baselines])
        avg_random_hit_rate = np.mean([b['hit_rate'] for b in random_baselines])
        
        freq_baseline = {
            "avg_matched": float(np.mean(freq_matches)),
            "hit_rate": float(sum(1 for m in freq_matches if m > 0) / evaluations)
        }
        
        weighted_freq_baseline = {
            "avg_matched": float(np.mean(weighted_freq_matches)),
            "hit_rate": float(sum(1 for m in weighted_freq_matches if m > 0) / evaluations)
        }
        
        avg_matched = total_matched / evaluations
        hit_rate = hits / evaluations
        
        better_than_random = avg_matched > avg_random_matched

        return BacktestResult(
            total_evaluations=evaluations,
            hit_rate=float(hit_rate),
            avg_matched=float(avg_matched),
            top_1_accuracy=float(top_1_hits / evaluations),
            top_5_accuracy=float(top_5_hits / evaluations),
            top_10_accuracy=float(top_10_hits / evaluations),
            precision=float(np.mean(precisions)),
            recall=float(np.mean(recalls)),
            brier_score=float(np.mean(brier_scores)),
            random_baseline={
                "avg_matched": float(avg_random_matched),
                "hit_rate": float(avg_random_hit_rate)
            },
            freq_baseline=freq_baseline,
            weighted_freq_baseline=weighted_freq_baseline,
            better_than_random=bool(better_than_random)
        )
