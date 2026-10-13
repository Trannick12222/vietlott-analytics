import math
import random
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, field
from .scoring import NumberScore

@dataclass
class Combination:
    numbers: List[int]
    strategy: str
    score: float
    fitness_score: float = 0.0
    sum_total: int = 0
    odd_even_ratio: str = ""
    delta_steps: List[int] = field(default_factory=list)
    rank: int = 0

    def to_dict(self) -> Dict:
        return {
            "rank": self.rank,
            "numbers": self.numbers,
            "strategy": self.strategy,
            "score": round(self.score, 2),
            "fitness_score": round(self.fitness_score, 1),
            "sum_total": self.sum_total,
            "odd_even_ratio": self.odd_even_ratio,
            "delta_steps": self.delta_steps
        }

@dataclass
class BaoCombination:
    bao_type: int
    numbers: List[int]
    strategy: str
    score: float
    ticket_count: int
    cost: int
    odd_count: int
    even_count: int
    low_count: int
    high_count: int

    def to_dict(self) -> Dict:
        return {
            "bao_type": self.bao_type,
            "numbers": self.numbers,
            "strategy": self.strategy,
            "score": round(self.score, 2),
            "ticket_count": self.ticket_count,
            "cost": self.cost,
            "odd_count": self.odd_count,
            "even_count": self.even_count,
            "low_count": self.low_count,
            "high_count": self.high_count,
            "odd_even_ratio": f"{self.odd_count}/{self.even_count}",
            "low_high_ratio": f"{self.low_count}/{self.high_count}"
        }

class CombinationGenerator:
    def __init__(self, max_number: int = 45, numbers_per_draw: int = 6):
        self.max_number = max_number
        self.numbers_per_draw = numbers_per_draw
        self.mid_point = max_number // 2
        
        # Kỳ vọng tổng Gaussian theo định lý giới hạn trung tâm
        self.mu_sum = (numbers_per_draw * (max_number + 1)) / 2.0
        self.sigma_sum = 33.7 if max_number == 45 else 44.5
        self.ideal_delta_avg = max_number / 6.0

    def _is_valid(self, combo: List[int], filter_odd_even: bool = True) -> bool:
        if len(combo) != self.numbers_per_draw:
            return False
        if len(set(combo)) != self.numbers_per_draw:
            return False
        if any(n < 1 or n > self.max_number for n in combo):
            return False
        
        if filter_odd_even:
            odds = sum(1 for n in combo if n % 2 != 0)
            if odds == 0 or odds == self.numbers_per_draw:
                return False
        
        return True

    def calculate_bao_tickets(self, bao_type: int) -> int:
        """Tính số vé quy đổi từ loại bao theo luật chơi Vietlott."""
        if bao_type == 5:
            return self.max_number - 5
        elif bao_type >= 7:
            return math.comb(bao_type, 6)
        return 1

    def calculate_bao_cost(self, bao_type: int) -> int:
        """Tính giá tiền (10.000 VNĐ / vé)."""
        return self.calculate_bao_tickets(bao_type) * 10_000

    def _evaluate_candidate(self, combo: List[int], scores: Dict[int, NumberScore], last_draw: Optional[List[int]] = None) -> Tuple[float, int, List[int], str]:
        """
        Đánh giá hàm thích nghi đa mục tiêu (Multi-Objective Fitness):
        1. Model Score của các bóng số (30%)
        2. Phân phối chuẩn Gaussian của tổng dãy số (20%)
        3. Phân bổ bước nhảy Delta tự nhiên (15%)
        4. Cân bằng chữ số đuôi và dải số Shannon (15%)
        5. Tỷ lệ Chẵn / Lẻ lý tưởng (10%)
        6. Độ trải rộng Span cực trị (10%)
        - Phạt nặng nếu vé có từ 3 số lặp lại từ kỳ liền trước (Xác suất lịch sử 0%).
        """
        s = sum(combo)
        z = (s - self.mu_sum) / self.sigma_sum
        gaussian_fit = math.exp(-0.5 * (z ** 2)) * 100.0

        deltas = [combo[i] - combo[i - 1] for i in range(1, len(combo))]
        avg_delta = sum(deltas) / float(len(deltas)) if deltas else 1.0
        # Bước nhảy tự nhiên: chỉ phạt nếu dồn quá nhiều số sát nhau (consecutives >= 3) hoặc khoảng cách cực đoan > 25
        consecutives_3 = sum(1 for i in range(len(deltas) - 1) if deltas[i] == 1 and deltas[i+1] == 1)
        extreme_deltas = sum(1 for d in deltas if d > 25)
        delta_penalty = consecutives_3 * 25.0 + extreme_deltas * 8.0
        delta_fit = max(0.0, 100.0 - abs(avg_delta - self.ideal_delta_avg) * 5.0 - delta_penalty)

        last_digits = [n % 10 for n in combo]
        unique_digits = len(set(last_digits))
        digit_fit = 100.0 if unique_digits >= 5 else (80.0 if unique_digits == 4 else 35.0)

        odds = sum(1 for n in combo if n % 2 != 0)
        evens = len(combo) - odds
        odd_even_fit = 100.0 if odds == 3 else (85.0 if odds in (2, 4) else 25.0)
        ratio_str = f"{evens}C : {odds}L"

        # Thống kê thứ tự cực trị: Độ trải rộng (Span = Max - Min)
        span = combo[-1] - combo[0]
        theo_span = (5.0 / 7.0) * (self.max_number + 1)
        span_fit = max(0.0, 100.0 - abs(span - theo_span) * 2.5)

        # Khống chế số lặp lại từ kỳ trước (Repeat Constraint Filter)
        repeat_penalty = 0.0
        if last_draw:
            repeats = len(set(combo) & set(last_draw))
            if repeats >= 3:
                repeat_penalty = 60.0  # Phạt cực nặng vì xác suất lặp >= 3 số trong lịch sử là 0%!
            elif repeats == 2:
                repeat_penalty = 12.0  # Phạt nhẹ nếu lặp 2 số (xác suất ~14%)

        model_sc = sum(scores[n].final_model_score for n in combo) / float(len(combo))

        base_fitness = (
            0.30 * model_sc +
            0.20 * gaussian_fit +
            0.15 * delta_fit +
            0.15 * digit_fit +
            0.10 * span_fit +
            0.10 * odd_even_fit
        )
        fitness = max(0.0, base_fitness - repeat_penalty)
        return fitness, s, deltas, ratio_str

    def generate(self, scores: Dict[int, NumberScore], num_per_strategy: int = 3, filter_odd_even: bool = True, last_draw: Optional[List[int]] = None) -> List[Combination]:
        """
        Tạo danh sách các bộ số bao quát 5 chiến lược toàn diện (mặc định đúng 15 dãy số):
        1. Tối Ưu Phong Độ (Elite Hot): tập trung bóng điểm cao, chuẩn Gauss.
        2. Cân Bằng Chu Kỳ (Balanced Rebound): 3 Hot + 3 Cold.
        3. Săn Số Gan / Dị Biệt (Cold Outbreak): 2 Hot + 4 Cold, tổng mở rộng dải cao, khởi đầu linh hoạt.
        4. Nén Dải Thấp (Statistical Compression): co cụm dải thấp <= 33/40, tổng nén.
        5. Bước Nhảy Delta (Random Spread): phân bổ đều 6 dải, chữ số đuôi đa dạng.
        - Khống chế: Tối đa chỉ cho phép 1 (tối đa 2) số lặp lại từ kỳ trước (last_draw), tuyệt đối loại bỏ các vé có >= 3 số lặp.
        """
        sorted_scores = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
        pool_size = min(len(sorted_scores), max(25, self.numbers_per_draw * 4))
        hot_nums = [s.number for s in sorted_scores[:pool_size]]
        cold_nums = [s.number for s in sorted_scores[-pool_size:]]

        low_bound = 33 if self.max_number == 45 else 40
        low_pool = [n for n in range(1, low_bound + 1)]
        hot_teen_nums = [n for n in hot_nums if n >= 10]
        if len(hot_teen_nums) < 12:
            extra_teens = [s.number for s in sorted_scores if s.number >= 10 and s.number not in hot_teen_nums]
            hot_teen_nums.extend(extra_teens[:15])

        # Sinh 5 tập ứng viên chuyên biệt:
        cand_elite = []
        cand_rebound = []
        cand_outbreak = []
        cand_low_comp = []
        cand_spread = []

        min_sum = int(self.mu_sum - self.sigma_sum)
        max_sum = int(self.mu_sum + self.sigma_sum)

        # 1. Elite (Hot): thuần Hot, tổng chuẩn Gauss
        for _ in range(1500):
            c = sorted(random.sample(hot_nums, self.numbers_per_draw))
            if last_draw and len(set(c) & set(last_draw)) >= 3:
                continue
            fit, s, deltas, ratio = self._evaluate_candidate(c, scores, last_draw=last_draw)
            if min_sum <= s <= max_sum and (ratio.startswith("3C") or ratio.startswith("2C") or ratio.startswith("4C")):
                cand_elite.append((fit, c, s, deltas, ratio))

        # 2. Rebound (Balanced): 3 Hot + 3 Cold
        for _ in range(1500):
            c = sorted(random.sample(hot_nums, 3) + random.sample(cold_nums, 3))
            if last_draw and len(set(c) & set(last_draw)) >= 3:
                continue
            fit, s, deltas, ratio = self._evaluate_candidate(c, scores, last_draw=last_draw)
            if (min_sum - 15) <= s <= (max_sum + 15):
                cand_rebound.append((fit, c, s, deltas, ratio))

        # 3. Outbreak (Cold Outbreak / Dị Biệt): 2 Hot + 4 Cold, tổng mở rộng dải cao
        for _ in range(2500):
            c = sorted(random.sample(hot_nums, 2) + random.sample(cold_nums, 4))
            if last_draw and len(set(c) & set(last_draw)) >= 3:
                continue
            fit, s, deltas, ratio = self._evaluate_candidate(c, scores, last_draw=last_draw)
            if (self.mu_sum - 10) <= s <= (self.mu_sum + 1.8 * self.sigma_sum):
                cand_outbreak.append((fit, c, s, deltas, ratio))

        # 4. Low Compression (Statistical): Nén dải thấp <= low_bound
        for _ in range(2000):
            c = sorted(random.sample(low_pool, self.numbers_per_draw))
            if last_draw and len(set(c) & set(last_draw)) >= 3:
                continue
            fit, s, deltas, ratio = self._evaluate_candidate(c, scores, last_draw=last_draw)
            if (self.mu_sum - 1.8 * self.sigma_sum) <= s <= (self.mu_sum + 5):
                cand_low_comp.append((fit, c, s, deltas, ratio))

        # 5. Delta Spread (Random Spread): phân bổ đều qua các dải buckets
        step = self.max_number / 6.0
        buckets = [[n for n in range(1, self.max_number + 1) if (i * step) < n <= ((i + 1) * step)] for i in range(6)]
        for _ in range(1500):
            c = sorted([random.choice(b) for b in buckets if b])
            if len(set(c)) == self.numbers_per_draw:
                if last_draw and len(set(c) & set(last_draw)) >= 3:
                    continue
                fit, s, deltas, ratio = self._evaluate_candidate(c, scores, last_draw=last_draw)
                cand_spread.append((fit, c, s, deltas, ratio))

        cand_elite.sort(key=lambda x: x[0], reverse=True)
        cand_rebound.sort(key=lambda x: x[0], reverse=True)
        cand_outbreak.sort(key=lambda x: x[0], reverse=True)
        cand_low_comp.sort(key=lambda x: x[0], reverse=True)
        cand_spread.sort(key=lambda x: x[0], reverse=True)

        def pick_diverse(candidates, count: int, existing_combos: List[List[int]]) -> List[Tuple]:
            selected = []
            for item in candidates:
                c = item[1]
                overlap = False
                for prev in existing_combos + [x[1] for x in selected]:
                    if len(set(c) & set(prev)) >= 5:
                        overlap = True
                        break
                if not overlap:
                    selected.append(item)
                    if len(selected) >= count:
                        break
            if len(selected) < count:
                for item in candidates:
                    if item not in selected:
                        selected.append(item)
                        if len(selected) >= count:
                            break
            return selected

        # Lựa chọn tổ hợp đa dạng theo số lượng yêu cầu num_per_strategy
        n_each = max(1, num_per_strategy)
        picked_combos = []

        sel_elite = pick_diverse(cand_elite, n_each, picked_combos)
        picked_combos.extend([x[1] for x in sel_elite])

        sel_rebound = pick_diverse(cand_rebound, n_each, picked_combos)
        picked_combos.extend([x[1] for x in sel_rebound])

        sel_outbreak = pick_diverse(cand_outbreak, n_each, picked_combos)
        picked_combos.extend([x[1] for x in sel_outbreak])

        sel_low_comp = pick_diverse(cand_low_comp, n_each, picked_combos)
        picked_combos.extend([x[1] for x in sel_low_comp])

        sel_spread = pick_diverse(cand_spread, n_each, picked_combos)

        tier_groups = [
            (sel_elite, "Tối Ưu Phong Độ (Elite Hot)"),
            (sel_rebound, "Cân Bằng Chu Kỳ (Balanced Rebound)"),
            (sel_outbreak, "Săn Số Gan / Dị Biệt (Cold Outbreak)"),
            (sel_low_comp, "Nén Dải Thấp (Statistical Compression)"),
            (sel_spread, "Bước Nhảy Delta (Random Spread)")
        ]

        results = []
        rank = 1
        for group_items, strat_name in tier_groups:
            for fit, c, s, deltas, ratio in group_items:
                sc = sum(scores[n].final_model_score for n in c) / float(len(c))
                results.append(Combination(
                    numbers=c,
                    strategy=strat_name,
                    score=sc,
                    fitness_score=fit,
                    sum_total=s,
                    odd_even_ratio=ratio,
                    delta_steps=deltas,
                    rank=rank
                ))
                rank += 1

        target_total = num_per_strategy * 5
        return results[:target_total] if len(results) >= target_total else results

    def _build_bao_object(self, numbers: List[int], strategy: str, scores: Dict[int, NumberScore], bao_type: int) -> BaoCombination:
        sorted_nums = sorted(numbers)
        avg_score = sum(scores[n].final_model_score for n in sorted_nums) / len(sorted_nums) if sorted_nums else 0.0
        odds = sum(1 for n in sorted_nums if n % 2 != 0)
        evens = len(sorted_nums) - odds
        lows = sum(1 for n in sorted_nums if n <= self.mid_point)
        highs = len(sorted_nums) - lows
        tickets = self.calculate_bao_tickets(bao_type)
        cost = self.calculate_bao_cost(bao_type)

        return BaoCombination(
            bao_type=bao_type,
            numbers=sorted_nums,
            strategy=strategy,
            score=avg_score,
            ticket_count=tickets,
            cost=cost,
            odd_count=odds,
            even_count=evens,
            low_count=lows,
            high_count=highs
        )

    def generate_bao(
        self,
        scores: Dict[int, NumberScore],
        bao_type: int = 7,
        num_per_strategy: int = 1,
        last_draw: Optional[List[int]] = None
    ) -> List[BaoCombination]:
        """Sinh các dàn số Bao tối ưu có khống chế trần số lặp lại từ kỳ liền trước."""
        valid_baos = [5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 18]
        if bao_type not in valid_baos:
            bao_type = 7

        k = bao_type
        sorted_scores = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
        all_numbers = [s.number for s in sorted_scores]
        pool_size = min(len(sorted_scores), max(k + 6, 20))
        hot_pool = [s.number for s in sorted_scores[:pool_size]]
        cold_pool = [s.number for s in sorted_scores[-pool_size:]]

        # Nới lỏng khống chế lặp: Cho phép linh hoạt tới 2 số rơi tự do (Back-to-back)
        max_repeats = 2 if k >= 7 else 1

        def enforce_repeat_limit(combo_nums: List[int], candidates_pool: List[int]) -> List[int]:
            if not last_draw:
                return combo_nums
            last_draw_set = set(last_draw)
            in_last = [n for n in combo_nums if n in last_draw_set]
            if len(in_last) <= max_repeats:
                return combo_nums

            in_last_sorted = sorted(in_last, key=lambda n: scores[n].final_model_score, reverse=True)
            to_remove = set(in_last_sorted[max_repeats:])

            clean_combo = [n for n in combo_nums if n not in to_remove]
            available = [n for n in candidates_pool if n not in last_draw_set and n not in clean_combo]
            available_sorted = sorted(available, key=lambda n: scores[n].final_model_score, reverse=True)
            needed = k - len(clean_combo)
            clean_combo.extend(available_sorted[:needed])

            if len(clean_combo) < k:
                more_avail = [n for n in all_numbers if n not in clean_combo and n not in to_remove]
                clean_combo.extend(more_avail[:k - len(clean_combo)])

            return clean_combo[:k]

        results = []

        # 1. Chiến lược: Tối ưu Model Score (Hot Elite)
        top_candidates = hot_pool[:min(len(hot_pool), k + 4)]
        best_combo_s1 = sorted(top_candidates[:k])
        odds_s1 = sum(1 for n in best_combo_s1 if n % 2 != 0)
        if (odds_s1 == 0 or odds_s1 == k) and len(top_candidates) > k:
            for extra in top_candidates[k:]:
                if (odds_s1 == 0 and extra % 2 != 0) or (odds_s1 == k and extra % 2 == 0):
                    best_combo_s1[-1] = extra
                    break
        best_combo_s1 = enforce_repeat_limit(best_combo_s1, all_numbers)
        results.append(self._build_bao_object(best_combo_s1, "Tối ưu Model Score", scores, k))

        # 2. Chiến lược: Cân bằng Hot & Cold (Balanced Rebound)
        hot_count = max(3, int(round(k * 0.6)))
        combo_s2 = list(hot_pool[:hot_count])
        for c_num in cold_pool:
            if len(combo_s2) >= k:
                break
            if c_num not in combo_s2:
                combo_s2.append(c_num)
        combo_s2 = enforce_repeat_limit(combo_s2, all_numbers)
        results.append(self._build_bao_object(combo_s2, "Cân bằng Hot & Cold", scores, k))

        # 3. Chiến lược: Trải Đều Dải Số - Bước Nhảy Rộng (Wide Delta Spread - 6 Buckets)
        # Chia thành 6 phân vùng bao quát trọn vẹn từ 1 đến max_number
        step = self.max_number / 6.0
        buckets = [
            [n for n in all_numbers if (i * step) < n <= ((i + 1) * step)]
            for i in range(6)
        ]
        spread_combo = []
        tier = 0
        while len(spread_combo) < k:
            added_in_round = False
            for b in buckets:
                top_in_b = sorted(b, key=lambda n: scores[n].final_model_score, reverse=True)
                if len(top_in_b) > tier and top_in_b[tier] not in spread_combo:
                    spread_combo.append(top_in_b[tier])
                    added_in_round = True
                    if len(spread_combo) >= k:
                        break
            tier += 1
            if not added_in_round:
                break
        spread_combo = enforce_repeat_limit(spread_combo, all_numbers)
        results.append(self._build_bao_object(spread_combo, "Phân bổ Đều Dải Số", scores, k))

        # 4. Chiến lược: Săn Số Gan (Cold Outbreak - Dị Biệt)
        hot_count_s4 = max(2, int(round(k * 0.3)))
        combo_s4 = list(hot_pool[:hot_count_s4])
        for c_num in cold_pool:
            if len(combo_s4) >= k:
                break
            if c_num not in combo_s4:
                combo_s4.append(c_num)
        combo_s4 = enforce_repeat_limit(combo_s4, all_numbers)
        results.append(self._build_bao_object(combo_s4, "Săn Số Gan (Cold Outbreak)", scores, k))

        # 5. Chiến lược: Nén Dải Thấp (Statistical Compression)
        low_limit = 33 if self.max_number == 45 else 40
        low_pool_candidates = [n for n in all_numbers if n <= low_limit]
        top_low_deterministic = sorted(low_pool_candidates, key=lambda n: scores[n].final_model_score, reverse=True)
        combo_s5 = list(top_low_deterministic[:k])
        if len(combo_s5) < k:
            for extra in all_numbers:
                if extra not in combo_s5:
                    combo_s5.append(extra)
                if len(combo_s5) >= k:
                    break
        combo_s5 = enforce_repeat_limit(combo_s5, low_pool_candidates)
        results.append(self._build_bao_object(combo_s5, "Nén Dải Thấp (Rút Thấp)", scores, k))

        return results


def generate_combinations(n_combinations: int = 5, game_type: str = "mega", filter_odd_even: bool = True, strategy: Optional[str] = None) -> List[List[int]]:
    """Convenience helper to generate list of number combinations."""
    max_num = 45 if "mega" in str(game_type).lower() else 55
    generator = CombinationGenerator(max_number=max_num, numbers_per_draw=6)
    dummy_scores = {n: NumberScore(number=n, final_model_score=50.0) for n in range(1, max_num + 1)}
    all_combos = generator.generate(dummy_scores, num_per_strategy=max(n_combinations, 5), filter_odd_even=filter_odd_even)
    
    if strategy:
        matched = [c.numbers for c in all_combos if strategy.lower() in c.strategy.lower()]
        if matched:
            return matched[:n_combinations]
    return [c.numbers for c in all_combos[:n_combinations]]
