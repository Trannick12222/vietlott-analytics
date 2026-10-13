import logging
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from src.config.settings import LotteryType, LOTTERY_CONFIGS, settings
from src.database.repository import DatabaseRepository
from src.database.models import Draw, FetchLog
from src.fetcher.manager import FetchManager
from src.statistics.engine import analyze_all
from src.prediction.scoring import EnsembleScoringEngine, NumberScore
from src.prediction.combination import CombinationGenerator
from src.prediction.wheeling import WheelingEngine
from src.simulation.monte_carlo import MonteCarloSimulator
from src.api.schemas import (
    DrawResponse, FetchRequest
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.repo = DatabaseRepository(db_session)
    
    def _draw_to_numbers(self, draw: Draw) -> List[int]:
        """Extract the 6 main numbers from a Draw ORM object."""
        return [draw.number_1, draw.number_2, draw.number_3,
                draw.number_4, draw.number_5, draw.number_6]
    
    def _draws_to_number_lists(self, draws: List[Draw]) -> List[List[int]]:
        """Convert list of Draw ORM objects to list of number lists."""
        return [self._draw_to_numbers(d) for d in draws]
    
    def _build_raw_scores(self, stats_result, config) -> Dict[str, Dict[int, float]]:
        """Extract raw scores from StatisticalResult to feed into EnsembleScoringEngine."""
        raw = {}
        
        # Frequency scores
        freq = stats_result.frequency
        if isinstance(freq, dict):
            raw['frequency'] = freq.get('frequency_pct', {})
            raw['weighted_frequency'] = freq.get('weighted_frequency', {})
        
        # Recency scores - convert gaps to scores (higher gap = lower recency score)
        # Bổ sung bộ giảm tải bão hòa (Saturation Penalty): nếu số đã nổ >= 3 lần trong 4-5 kỳ gần nhất,
        # xác suất thống kê tiếp tục nổ liên tục suy giảm mạnh (Mean Reversion), cần hạ điểm recency.
        recency = stats_result.recency
        freq_dict = stats_result.frequency if isinstance(stats_result.frequency, dict) else {}
        recent_5_counts = freq_dict.get('recent_5_counts', {})
        if isinstance(recency, dict):
            gaps = recency.get('gaps', {})
            max_gap = max(gaps.values()) if gaps else 1
            rec_scores = {}
            for num, gap in gaps.items():
                base_rec = max(0, max_gap - gap)
                # Nếu đã nổ 3 lần trong 5 kỳ -> phạt 40% điểm phong độ
                r5 = recent_5_counts.get(num, 0)
                if r5 >= 3:
                    base_rec *= 0.55  # Bão hòa cực điểm, ép giảm điểm
                elif r5 == 2 and gap == 0:
                    base_rec *= 0.80  # Đã nổ 2 kỳ liên tiếp
                rec_scores[num] = base_rec
            raw['recency'] = rec_scores
        
        # Bayesian scores
        bayesian = stats_result.bayesian
        if isinstance(bayesian, dict):
            raw['bayesian'] = bayesian.get('posterior_mean', {})
        
        # Correlation co-occurrence scores (average co-occurrence for each number)
        correlation = stats_result.correlation
        if isinstance(correlation, dict):
            pair_freq = correlation.get('pair_frequency', {})
            co_scores = {}
            for num in range(1, config.max_number + 1):
                total = 0
                count = 0
                for (a, b), freq_val in pair_freq.items():
                    if a == num or b == num:
                        total += freq_val
                        count += 1
                co_scores[num] = total / count if count > 0 else 0
            raw['co_occurrence'] = co_scores
        
        # Distribution scores - range distribution
        dist = stats_result.distribution
        if isinstance(dist, dict):
            bucket_dist = dist.get('bucket_distribution', {})
            range_scores = {}
            for num in range(1, config.max_number + 1):
                for bucket_name, count in bucket_dist.items():
                    range_scores[num] = range_scores.get(num, 0) + count
            raw['range_dist'] = range_scores if range_scores else {n: 50 for n in range(1, config.max_number + 1)}
            
            # Odd/even balance
            raw['odd_even'] = {n: 50 for n in range(1, config.max_number + 1)}  # neutral default

        # Regime & Mean Reversion scores (Bổ sung 4 công thức toán học chuyên sâu)
        regime = getattr(stats_result, 'regime', {})
        if isinstance(regime, dict):
            mean_rev = regime.get('mean_reversion', {})
            per_num_rev = mean_rev.get('per_number_scores', {})
            raw['regime_reversion'] = per_num_rev if per_num_rev else {n: 50.0 for n in range(1, config.max_number + 1)}
        else:
            raw['regime_reversion'] = {n: 50.0 for n in range(1, config.max_number + 1)}
        
        return raw

    def _get_scored_engine(self, lottery_type: LotteryType):
        """Helper to compute statistics and ensemble scores for a lottery type."""
        draws = self.repo.get_all_draws(lottery_type)
        if not draws:
            return None, None, None, None
        
        config = LOTTERY_CONFIGS[lottery_type]
        draw_lists = self._draws_to_number_lists(draws)
        stats = analyze_all(draw_lists, lottery_type=config.stat_type, decay_factor=settings.DECAY_FACTOR)
        
        raw_scores = self._build_raw_scores(stats, config)
        mc = MonteCarloSimulator(config.max_number, config.numbers_per_draw)
        mc_result = mc.run_simulation(min(settings.MONTE_CARLO_SIMULATIONS, 50000))
        raw_scores['monte_carlo'] = mc_result.number_probabilities
        
        scoring = EnsembleScoringEngine(config.max_number)
        scores = scoring.calculate_ensemble_scores(raw_scores)
        return draws, config, stats, scores
    
    def get_latest_draws(self, lottery_type: LotteryType, limit: int = 100) -> List[DrawResponse]:
        draws = self.repo.get_latest_draws(lottery_type, limit)
        responses = []
        for d in draws:
            responses.append(DrawResponse(
                id=d.id,
                lottery_type=d.lottery_type.value if isinstance(d.lottery_type, LotteryType) else str(d.lottery_type),
                draw_number=d.draw_number,
                draw_date=d.draw_date,
                numbers=self._draw_to_numbers(d),
                jackpot_2=d.jackpot_2,
                source=d.source or "unknown"
            ))
        return responses
    
    def get_statistics(self, lottery_type: LotteryType) -> Optional[Dict[str, Any]]:
        draws = self.repo.get_all_draws(lottery_type)
        if not draws:
            return None
        
        config = LOTTERY_CONFIGS[lottery_type]
        draw_lists = self._draws_to_number_lists(draws)
        stats = analyze_all(draw_lists, lottery_type=config.stat_type, decay_factor=settings.DECAY_FACTOR)
        
        warnings = []
        if len(draws) < 30:
            warnings.append(f"Cỡ mẫu quá nhỏ ({len(draws)} kỳ). Dữ liệu chưa đủ độ tin cậy thống kê.")
        elif len(draws) < 100:
            warnings.append(f"Kho dữ liệu hiện có {len(draws)} kỳ. Đang tiếp tục mở rộng để đạt ý nghĩa thống kê cao hơn.")
        
        return {
            "total_draws": len(draws),
            "frequency": stats.frequency,
            "recency": stats.recency,
            "distribution": stats.distribution,
            "consecutive": stats.consecutive,
            "correlation": stats.correlation,
            "bayesian": stats.bayesian,
            "probability": stats.probability,
            "regime": getattr(stats, 'regime', {}),
            "warnings": warnings
        }
    
    def get_predictions(self, lottery_type: LotteryType, threshold: float = 50.0) -> Optional[Dict[str, Any]]:
        draws, config, stats, scores = self._get_scored_engine(lottery_type)
        if not draws:
            return None
        
        ranked = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
        
        # Build rankings
        rankings = []
        freq_data = stats.frequency
        recency_data = stats.recency
        bayesian_data = stats.bayesian
        
        for rank_idx, ns in enumerate(ranked, 1):
            num = ns.number
            freq_count = freq_data.get('counts', {}).get(num, 0) if isinstance(freq_data, dict) else 0
            recent_count = freq_data.get('recent_5_counts', {}).get(num, 0) if isinstance(freq_data, dict) else 0
            gap = recency_data.get('gaps', {}).get(num, 0) if isinstance(recency_data, dict) else 0
            bayes_est = bayesian_data.get('posterior_mean', {}).get(num, config.baseline_probability) if isinstance(bayesian_data, dict) else config.baseline_probability
            
            rankings.append({
                "rank": rank_idx,
                "number": num,
                "model_score": round(ns.final_model_score, 2),
                "mathematical_probability": round(config.baseline_probability * 100, 2),
                "frequency": f"{freq_count}/{len(draws)}",
                "recent_frequency": f"{recent_count}/5",
                "last_seen": f"{gap} kỳ trước" if gap > 0 else "Kỳ vừa rồi",
                "gap": gap,
                "bayesian_estimate": round(bayes_est, 4),
                "confidence": ns.confidence_level,
                "frequency_score": round(ns.frequency_score, 1),
                "recency_score": round(ns.recency_score, 1),
                "bayesian_score": round(ns.bayesian_score, 1),
                "weighted_score": round(ns.weighted_frequency_score, 1),
                "co_occurrence_score": round(ns.co_occurrence_score, 1),
                "regime_score": round(ns.regime_score, 1),
                "monte_carlo_score": round(ns.monte_carlo_score, 1)
            })
        
        # Filter by threshold
        filtered = [r for r in rankings if r['model_score'] >= threshold]
        
        # Generate combinations (Đúng 15 dãy số siêu tối ưu)
        last_draw = self._draw_to_numbers(draws[-1]) if draws else []
        combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
        combos = combo_gen.generate(scores, num_per_strategy=3, last_draw=last_draw)
        combo_responses = [c.to_dict() for c in combos]
        
        sample_warning = None
        if len(draws) < 30:
            sample_warning = f"CẢNH BÁO: Cỡ mẫu hiện tại nhỏ ({len(draws)} kỳ). Kết quả chỉ mang tính tham khảo thống kê."
        elif len(draws) < 100:
            sample_warning = f"Lưu ý: Phân tích dựa trên {len(draws)} kỳ quay."
        
        ml_warning = None
        if len(draws) < 50:
            ml_warning = "Mô hình Machine Learning tạm tắt do cỡ mẫu cần ít nhất 50 kỳ để hội tụ chuẩn xác."
        
        return {
            "rankings": filtered,
            "all_rankings": rankings,
            "combinations": combo_responses,
            "mathematical_probability": round(config.baseline_probability * 100, 2),
            "threshold": threshold,
            "no_numbers_passed": len(filtered) == 0,
            "regime_forecast": getattr(stats, 'regime', {}),
            "disclaimer": "LƯU Ý: Model Score là điểm số định lượng dựa trên phân tích thống kê lịch sử nhiều chiều, KHÔNG PHẢI xác suất trúng thưởng thực tế. Xổ số là biến cố ngẫu nhiên độc lập.",
            "sample_size_warning": sample_warning,
            "ml_warning": ml_warning,
            "total_draws": len(draws)
        }

    def get_bao_combinations(self, lottery_type: LotteryType, bao_type: int = 7) -> Optional[Dict[str, Any]]:
        """Tạo dàn vé Bao dựa trên phân tích Model Score và cân bằng cấu trúc xác suất."""
        draws, config, stats, scores = self._get_scored_engine(lottery_type)
        if not draws:
            return None
        
        last_draw = self._draw_to_numbers(draws[-1]) if draws else []
        combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
        bao_combos = combo_gen.generate_bao(scores, bao_type=bao_type, num_per_strategy=1, last_draw=last_draw)
        combo_dicts = [c.to_dict() for c in bao_combos]

        ticket_count = bao_combos[0].ticket_count if bao_combos else 0
        cost = bao_combos[0].cost if bao_combos else 0

        return {
            "lottery_type": lottery_type.value,
            "bao_type": bao_type,
            "ticket_count": ticket_count,
            "cost": cost,
            "formatted_cost": f"{cost:,} VNĐ",
            "combinations": combo_dicts,
            "total_draws": len(draws)
        }

    def get_wheeling_combinations(self, lottery_type: LotteryType, wheel_size: int = 12, strategy: str = "balanced") -> Optional[Dict[str, Any]]:
        """Tạo dàn vé ma trận che phủ Wheeling System tiết kiệm chi phí."""
        draws, config, stats, scores = self._get_scored_engine(lottery_type)
        if not draws:
            return None

        last_draw = self._draw_to_numbers(draws[-1]) if draws else []
        engine = WheelingEngine(config.max_number)
        wheel_res = engine.generate_wheel(scores, wheel_size=wheel_size, strategy=strategy, last_draw=last_draw)
        res_dict = wheel_res.to_dict()
        res_dict["lottery_type"] = lottery_type.value
        res_dict["total_draws"] = len(draws)
        return res_dict

    def optimize_custom_pool(self, lottery_type: LotteryType, custom_numbers: List[int], ticket_count: int = 8) -> Optional[Dict[str, Any]]:
        """
        Nhận dàn số tự chọn của người dùng (từ 7 đến 20 số),
        duyệt qua toàn bộ tổ hợp C(k, 6),
        chấm điểm theo 17 công thức và chọn ra N vé tối ưu nhất.
        """
        import itertools
        draws, config, stats, scores = self._get_scored_engine(lottery_type)
        if not draws:
            return None

        clean_nums = sorted(list(set([n for n in custom_numbers if 1 <= n <= config.max_number])))
        if len(clean_nums) < 6:
            return {"error": "Cần ít nhất 6 con số hợp lệ trong phạm vi bảng số."}
        if len(clean_nums) > 20:
            clean_nums = clean_nums[:20]

        all_combos = list(itertools.combinations(clean_nums, 6))
        total_possible = len(all_combos)

        combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
        evaluated = []

        regime_data = getattr(stats, 'regime', {})
        regime_analysis = regime_data.get('regime_analysis', {}) if isinstance(regime_data, dict) else {}
        forecast = regime_analysis.get('next_draw_forecast', {})
        predicted_regime = forecast.get('predicted_regime', 'STD')
        exp_min_range = forecast.get('expected_min_range', [1, 15])
        exp_max_range = forecast.get('expected_max_range', [35, config.max_number])
        exp_sum_range = forecast.get('expected_sum_range', [120, 200])

        low_threshold = 33 if config.stat_type == 'mega' else 40
        std_threshold = 42 if config.stat_type == 'mega' else 50

        last_draw = self._draw_to_numbers(draws[-1]) if draws else []

        for c in all_combos:
            c_list = list(c)
            fit, s, deltas, ratio = combo_gen._evaluate_candidate(c_list, scores, last_draw=last_draw)
            odds = sum(1 for x in c_list if x % 2 != 0)
            lows = sum(1 for x in c_list if x <= config.low_high_boundary)

            c_min = c_list[0]
            c_max = c_list[-1]
            if c_max <= low_threshold:
                regime_match_label = "Nén Dải Thấp (Rút thấp)"
                regime_match_code = "LOW"
            elif c_max > std_threshold:
                regime_match_label = "Bung Dải Cao (Cực đại)"
                regime_match_code = "HIGH"
            else:
                regime_match_label = "Cân Bằng Chuẩn (Gauss)"
                regime_match_code = "STD"

            # Điểm cộng thích ứng theo dự báo nhịp kỳ tới
            regime_bonus = 0.0
            if regime_match_code == predicted_regime:
                regime_bonus += 12.0
            if exp_min_range[0] <= c_min <= exp_min_range[1]:
                regime_bonus += 4.0
            if exp_max_range[0] <= c_max <= exp_max_range[1]:
                regime_bonus += 4.0
            if exp_sum_range[0] <= s <= exp_sum_range[1]:
                regime_bonus += 5.0

            total_fitness = fit + regime_bonus

            evaluated.append({
                "numbers": c_list,
                "fitness": round(total_fitness, 1),
                "base_fitness": round(fit, 1),
                "regime_bonus": round(regime_bonus, 1),
                "regime_label": regime_match_label,
                "regime_code": regime_match_code,
                "is_forecast_match": (regime_match_code == predicted_regime),
                "sum": s,
                "odd_even": ratio,
                "low_high": f"{lows}T : {6 - lows}C",
                "delta_str": " - ".join(str(d) for d in deltas)
            })

        evaluated.sort(key=lambda x: x["fitness"], reverse=True)

        selected = []
        for item in evaluated:
            c = item["numbers"]
            too_close = False
            for prev in selected:
                if len(set(c) & set(prev["numbers"])) >= 5:
                    too_close = True
                    break
            if not too_close:
                selected.append(item)
            if len(selected) >= ticket_count:
                break

        if len(selected) < ticket_count:
            for item in evaluated:
                if item not in selected:
                    selected.append(item)
                    if len(selected) >= ticket_count:
                        break

        # Đánh giá độ phủ tổ hợp 3 số
        all_triplets = list(itertools.combinations(clean_nums, 3))
        selected_sets = [set(item["numbers"]) for item in selected]
        hits_3 = sum(1 for trip in all_triplets if any(len(set(trip) & s) >= 3 for s in selected_sets))
        trip_coverage_pct = round((hits_3 / float(len(all_triplets))) * 100.0, 1) if all_triplets else 100.0

        cost = len(selected) * 10_000
        full_bao_cost = total_possible * 10_000

        suitability = self.evaluate_pool_suitability(custom_numbers)

        return {
            "lottery_type": lottery_type.value,
            "custom_numbers": clean_nums,
            "pool_size": len(clean_nums),
            "total_possible_combinations": total_possible,
            "ticket_count": len(selected),
            "cost": cost,
            "formatted_cost": f"{cost:,} VNĐ",
            "full_bao_cost": full_bao_cost,
            "formatted_full_bao_cost": f"{full_bao_cost:,} VNĐ",
            "savings": full_bao_cost - cost,
            "formatted_savings": f"{full_bao_cost - cost:,} VNĐ",
            "savings_pct": round(((full_bao_cost - cost) / float(full_bao_cost)) * 100.0, 1) if full_bao_cost > 0 else 0,
            "triplet_coverage_pct": trip_coverage_pct,
            "regime_forecast": forecast,
            "suitability": suitability,
            "tickets": selected
        }

    def evaluate_pool_suitability(self, custom_numbers: List[int]) -> Dict[str, Any]:
        """
        Đánh giá tính tương thích và khuyến nghị dàn số tự chọn phù hợp hơn cho MEGA 6/45 hay POWER 6/55.
        Dựa trên 4 tiêu chí toán học:
        1. Giới hạn biên số lớn (> 45 chỉ có thể là Power 6/55)
        2. Độ lệch tâm Gaussian (khoảng cách đến 138 của 6/45 vs 168 của 6/55)
        3. Phân bổ dải số (độ phủ trên 5 dải số của từng loại hình)
        4. Tương quan Model Score thực nghiệm trên 100 kỳ gần nhất
        """
        import numpy as np

        clean_nums = sorted(list(set([int(n) for n in custom_numbers if 1 <= n <= 55])))
        if len(clean_nums) < 6:
            return {
                "error": "Cần ít nhất 6 số hợp lệ.",
                "recommended": "MEGA_645",
                "recommended_label": "Mega 6/45",
                "mega_pct": 50.0,
                "power_pct": 50.0,
                "is_mandatory": False,
                "reasons": ["Chưa đủ 6 số để đánh giá tương thích."]
            }

        has_over_45 = any(n > 45 for n in clean_nums)
        reasons = []

        # Nếu có số > 45, bắt buộc 100% là POWER 6/55
        if has_over_45:
            over_nums = [n for n in clean_nums if n > 45]
            over_str = ", ".join(f"{n:02d}" for n in over_nums)
            reasons.append(f"Dàn số có chứa các số > 45 ({over_str}), bắt buộc phải chơi POWER 6/55 vì Mega 6/45 chỉ quay từ 01 đến 45.")
            return {
                "recommended": "POWER_655",
                "recommended_label": "Power 6/55",
                "mega_pct": 0.0,
                "power_pct": 100.0,
                "is_mandatory": True,
                "reasons": reasons,
                "expected_sum": round(float(np.mean(clean_nums) * 6), 1)
            }

        # Nếu tất cả các số <= 45: tính toán định lượng
        avg_num = float(np.mean(clean_nums))
        exp_sum = avg_num * 6.0

        # Tiêu chí 1: Độ lệch Gaussian Sum
        z_mega = abs(exp_sum - 138.0) / 33.0
        z_power = abs(exp_sum - 168.0) / 37.0
        fit_sum_mega = math.exp(-0.5 * (z_mega ** 2)) * 100.0
        fit_sum_power = math.exp(-0.5 * (z_power ** 2)) * 100.0

        # Tiêu chí 2: Độ che phủ dải số
        mega_buckets = [(1,9), (10,18), (19,27), (28,36), (37,45)]
        power_buckets = [(1,11), (12,22), (23,33), (34,44), (45,55)]

        covered_mega = sum(1 for b in mega_buckets if any(b[0] <= n <= b[1] for n in clean_nums))
        covered_power = sum(1 for b in power_buckets if any(b[0] <= n <= b[1] for n in clean_nums))
        has_bucket_5_power = any(45 <= n <= 55 for n in clean_nums)

        bucket_score_mega = (covered_mega / 5.0) * 100.0
        bucket_score_power = (covered_power / 5.0) * 100.0 if has_bucket_5_power else ((covered_power / 5.0) * 100.0 * 0.65)

        # Tiêu chí 3: Tương quan điểm số lịch sử Model Score
        draws_m, conf_m, stats_m, scores_m = self._get_scored_engine(LotteryType.MEGA_645)
        draws_p, conf_p, stats_p, scores_p = self._get_scored_engine(LotteryType.POWER_655)

        model_sc_mega = float(np.mean([scores_m[n].final_model_score for n in clean_nums if n in scores_m])) if scores_m else 50.0
        model_sc_power = float(np.mean([scores_p[n].final_model_score for n in clean_nums if n in scores_p])) if scores_p else 50.0

        adv_factor_mega = 1.15
        adv_factor_power = 0.95

        total_mega = (0.35 * fit_sum_mega + 0.35 * bucket_score_mega + 0.30 * model_sc_mega) * adv_factor_mega
        total_power = (0.35 * fit_sum_power + 0.35 * bucket_score_power + 0.30 * model_sc_power) * adv_factor_power

        sum_total = total_mega + total_power
        mega_pct = round((total_mega / sum_total) * 100.0, 1) if sum_total > 0 else 50.0
        power_pct = round(100.0 - mega_pct, 1)

        if mega_pct >= 52.0:
            rec = "MEGA_645"
            rec_label = "Mega 6/45"
            reasons.append(f"Tổng điểm kỳ vọng của dàn số là {exp_sum:.0f}, rơi sát tâm vàng 138 của Mega 6/45 hơn so với 168 của Power 6/55.")
            if not has_bucket_5_power:
                reasons.append("Dàn số hoàn toàn không có bóng ở dải cao (45–55). Nếu đánh Power 6/55 sẽ bị hổng 1/5 bảng số.")
            reasons.append("Mega 6/45 có xác suất trúng tự nhiên cao hơn gấp 3,5 lần Power 6/55.")
        else:
            rec = "POWER_655"
            rec_label = "Power 6/55"
            reasons.append(f"Dàn số thiên về dải trung bình cao (tổng kỳ vọng {exp_sum:.0f}), phù hợp hơn với trục 168 của Power 6/55.")
            reasons.append("Các con số này có điểm Model Score phong độ cao hơn trên lịch sử quay thưởng của Power 6/55.")

        return {
            "recommended": rec,
            "recommended_label": rec_label,
            "mega_pct": mega_pct,
            "power_pct": power_pct,
            "is_mandatory": False,
            "expected_sum": round(exp_sum, 1),
            "reasons": reasons
        }
    
    def get_backtest_results(self, lottery_type: LotteryType) -> Optional[Dict[str, Any]]:
        draws = self.repo.get_all_draws(lottery_type)
        if not draws or len(draws) < 5:
            return {"status": "insufficient_data", "message": f"Cần ít nhất 5 kỳ quay để chạy backtesting, hiện có {len(draws) if draws else 0}."}
        
        config = LOTTERY_CONFIGS[lottery_type]
        draw_lists = self._draws_to_number_lists(draws)
        
        window_size = min(len(draw_lists) - 1, 20)
        if window_size < 3:
            return {"status": "insufficient_data", "message": "Không đủ dữ liệu cho rolling window backtest."}
        
        import random
        import numpy as np
        
        model_matches = []
        random_matches = []
        freq_matches = []
        
        for i in range(window_size, len(draw_lists)):
            window = draw_lists[max(0, i - window_size):i]
            actual = set(draw_lists[i])
            
            stats = analyze_all(window, lottery_type=config.stat_type)
            freq_counts = stats.frequency.get('counts', {}) if isinstance(stats.frequency, dict) else {}
            sorted_nums = sorted(freq_counts.items(), key=lambda x: x[1], reverse=True)
            model_top_6 = set([n for n, _ in sorted_nums[:6]])
            model_matches.append(len(model_top_6 & actual))
            
            rand_sum = 0
            for _ in range(100):
                rand_pick = set(random.sample(range(1, config.max_number + 1), 6))
                rand_sum += len(rand_pick & actual)
            random_matches.append(rand_sum / 100)
            
            freq_matches.append(len(model_top_6 & actual))
        
        model_avg = float(np.mean(model_matches))
        random_avg = float(np.mean(random_matches))
        model_hit_rate = float(sum(1 for m in model_matches if m > 0) / len(model_matches))
        random_hit_rate_expected = 1.0 - (1.0 - 6/config.max_number) ** 6
        
        better_than_random = model_avg > random_avg
        
        return {
            "status": "completed",
            "total_evaluations": len(model_matches),
            "window_size": window_size,
            "model": {
                "avg_matched": round(model_avg, 3),
                "hit_rate": round(model_hit_rate, 3),
                "total_hits": sum(model_matches),
            },
            "random_baseline": {
                "avg_matched": round(random_avg, 3),
                "expected_hit_rate": round(random_hit_rate_expected, 3),
            },
            "better_than_random": better_than_random,
            "verdict": "Không có bằng chứng thống kê nào cho thấy có lợi thế dự đoán dài hạn." if not better_than_random else "Mô hình cho hiệu quả tương đương hoặc nhỉnh nhẹ so với ngẫu nhiên trong cỡ mẫu ngắn.",
            "disclaimer": "Kết quả quá khứ không cam đoan hay bảo đảm kết quả tương lai. Các kỳ quay là hoàn toàn độc lập."
        }
    
    def fetch_data(self, lottery_type: LotteryType, limit: int = 100) -> Dict[str, Any]:
        manager = FetchManager(self.repo, data_dir=settings.DATA_DIR)
        added, source = manager.sync_latest(lottery_type, limit)
        return {
            "records_added": added,
            "source": source,
            "lottery_type": lottery_type.value,
            "message": f"Đã nạp thành công {added} kỳ quay mới từ {source}" if added > 0 else "Dữ liệu đã cập nhật đầy đủ, không có kỳ quay mới"
        }
    
    def get_dashboard_data(self, lottery_type: LotteryType) -> Dict[str, Any]:
        draws = self.get_latest_draws(lottery_type, limit=100)
        stats = self.get_statistics(lottery_type)
        predictions = self.get_predictions(lottery_type)
        backtest = self.get_backtest_results(lottery_type)
        bao_combos = self.get_bao_combinations(lottery_type, bao_type=7)
        wheeling_combos = self.get_wheeling_combinations(lottery_type, wheel_size=12)
        
        last_log = self.db.query(FetchLog).filter(
            FetchLog.lottery_type == lottery_type
        ).order_by(FetchLog.fetch_date.desc()).first()
        
        return {
            "lottery_type": lottery_type.value,
            "latest_draws": draws,
            "statistics": stats,
            "predictions": predictions,
            "backtest": backtest,
            "bao_combinations": bao_combos,
            "wheeling_combinations": wheeling_combos,
            "last_fetch": last_log.fetch_date.isoformat() if last_log else None,
            "total_draws_in_db": len(self.repo.get_all_draws(lottery_type))
        }
