from dataclasses import dataclass, field
from typing import Dict, Optional

@dataclass
class ScoreWeights:
    frequency: float = 0.15
    weighted_frequency: float = 0.20
    recency: float = 0.15
    bayesian: float = 0.20
    co_occurrence: float = 0.10
    range_dist: float = 0.10
    odd_even_balance: float = 0.05
    monte_carlo: float = 0.05
    regime_reversion: float = 0.0
    
    def normalize(self):
        total = sum([self.frequency, self.weighted_frequency, self.recency, 
                     self.bayesian, self.co_occurrence, self.range_dist, 
                     self.odd_even_balance, self.monte_carlo, self.regime_reversion])
        if total > 0:
            self.frequency /= total
            self.weighted_frequency /= total
            self.recency /= total
            self.bayesian /= total
            self.co_occurrence /= total
            self.range_dist /= total
            self.odd_even_balance /= total
            self.monte_carlo /= total
            self.regime_reversion /= total

@dataclass
class NumberScore:
    number: int
    frequency_score: float = 0.0
    weighted_frequency_score: float = 0.0
    recency_score: float = 0.0
    bayesian_score: float = 0.0
    co_occurrence_score: float = 0.0
    range_dist_score: float = 0.0
    regime_score: float = 0.0
    odd_even_score: float = 0.0
    monte_carlo_score: float = 0.0
    final_model_score: float = 0.0
    confidence_level: str = "Low"
    is_saturated: bool = False

class EnsembleScoringEngine:
    """
    Combines scores from multiple analysis methods to produce a final ranking.
    IMPORTANT: The output 'Final Model Score' is an ensemble ranking metric,
    not a true mathematical probability of the number appearing.
    """
    def __init__(self, max_number: int, weights: Optional[ScoreWeights] = None):
        self.max_number = max_number
        self.weights = weights or ScoreWeights()
        self.weights.normalize()
        
    def _normalize_scores(self, scores: Dict[int, float]) -> Dict[int, float]:
        if not scores:
            return {}
        min_val = min(scores.values())
        max_val = max(scores.values())
        if max_val == min_val:
            return {k: 50.0 for k in scores.keys()}
        return {k: ((v - min_val) / (max_val - min_val)) * 100 for k, v in scores.items()}

    def calculate_ensemble_scores(self, raw_scores: Dict[str, Dict[int, float]]) -> Dict[int, NumberScore]:
        # Tự động cấp trọng số cho regime_reversion nếu có dữ liệu đầu vào
        weights = ScoreWeights(
            frequency=self.weights.frequency,
            weighted_frequency=self.weights.weighted_frequency,
            recency=self.weights.recency,
            bayesian=self.weights.bayesian,
            co_occurrence=self.weights.co_occurrence,
            range_dist=self.weights.range_dist,
            odd_even_balance=self.weights.odd_even_balance,
            monte_carlo=self.weights.monte_carlo,
            regime_reversion=self.weights.regime_reversion if self.weights.regime_reversion > 0 else (0.10 if 'regime_reversion' in raw_scores else 0.0)
        )
        weights.normalize()

        freq = self._normalize_scores(raw_scores.get('frequency', {}))
        w_freq = self._normalize_scores(raw_scores.get('weighted_frequency', {}))
        rec = self._normalize_scores(raw_scores.get('recency', {}))
        bayes = self._normalize_scores(raw_scores.get('bayesian', {}))
        co = self._normalize_scores(raw_scores.get('co_occurrence', {}))
        ran = self._normalize_scores(raw_scores.get('range_dist', {}))
        regime = self._normalize_scores(raw_scores.get('regime_reversion', {}))
        oe = self._normalize_scores(raw_scores.get('odd_even', {}))
        mc = self._normalize_scores(raw_scores.get('monte_carlo', {}))
        saturated = raw_scores.get('saturated_numbers', {})
        
        results = {}
        for num in range(1, self.max_number + 1):
            score = NumberScore(number=num)
            score.frequency_score = freq.get(num, 0.0)
            score.weighted_frequency_score = w_freq.get(num, 0.0)
            score.recency_score = rec.get(num, 0.0)
            score.bayesian_score = bayes.get(num, 0.0)
            score.co_occurrence_score = co.get(num, 0.0)
            score.range_dist_score = ran.get(num, 0.0)
            score.regime_score = regime.get(num, 0.0)
            score.odd_even_score = oe.get(num, 0.0)
            score.monte_carlo_score = mc.get(num, 0.0)
            
            score.final_model_score = (
                score.frequency_score * weights.frequency +
                score.weighted_frequency_score * weights.weighted_frequency +
                score.recency_score * weights.recency +
                score.bayesian_score * weights.bayesian +
                score.co_occurrence_score * weights.co_occurrence +
                score.range_dist_score * weights.range_dist +
                score.regime_score * weights.regime_reversion +
                score.odd_even_score * weights.odd_even_balance +
                score.monte_carlo_score * weights.monte_carlo
            )

            # Phạt quá nhiệt nếu số nổ >= 3 lần trong 5 kỳ (Mean Reversion cạn kiệt)
            if num in saturated:
                score.is_saturated = True
                score.final_model_score = max(5.0, score.final_model_score - 20.0)
            
            # Simple confidence calculation based on variance of top 3 weights
            components = [score.weighted_frequency_score, score.bayesian_score, score.recency_score]
            mean_c = sum(components) / 3
            variance = sum((x - mean_c)**2 for x in components) / 3
            if score.is_saturated:
                score.confidence_level = "Low"
            elif variance < 100:
                score.confidence_level = "High"
            elif variance < 400:
                score.confidence_level = "Medium"
            else:
                score.confidence_level = "Low"
                
            results[num] = score
        return results
