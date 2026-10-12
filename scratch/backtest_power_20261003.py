import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import SessionLocal
from src.database.models import Draw
from src.config.settings import LotteryType, LOTTERY_CONFIGS, settings
from src.statistics.engine import analyze_all
from src.prediction.scoring import EnsembleScoringEngine
from src.prediction.combination import CombinationGenerator
from src.simulation.monte_carlo import MonteCarloSimulator
from src.api.service import AnalyticsService

def run_backtest():
    db = SessionLocal()
    # Lấy các kỳ đến ngày 2026-10-01
    draws = db.query(Draw).filter(
        Draw.lottery_type == LotteryType.POWER_655,
        Draw.draw_date <= '2026-10-01'
    ).order_by(Draw.draw_date.asc()).all()

    target_numbers = [7, 11, 13, 16, 18, 54]
    print(f"Tổng số kỳ phân tích (<= 2026-10-01): {len(draws)} kỳ")
    print(f"Kỳ mới nhất trong tập huấn luyện: Kỳ {draws[-1].draw_number} ({draws[-1].draw_date})")
    print(f"Bộ số mục tiêu cần dự đoán (03/10/2026): {target_numbers}\n")

    service = AnalyticsService(db)
    draw_lists = service._draws_to_number_lists(draws)
    config = LOTTERY_CONFIGS[LotteryType.POWER_655]

    # 1. Phân tích thống kê
    stats = analyze_all(draw_lists, lottery_type="power", decay_factor=settings.DECAY_FACTOR)
    raw_scores = service._build_raw_scores(stats, config)

    # Monte Carlo
    mc = MonteCarloSimulator(config.max_number, config.numbers_per_draw)
    mc_result = mc.run_simulation(100000)
    raw_scores['monte_carlo'] = mc_result.number_probabilities

    # 2. Chấm điểm Ensemble Scoring
    scoring = EnsembleScoringEngine(config.max_number)
    scores = scoring.calculate_ensemble_scores(raw_scores)

    ranked = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
    rankings_map = {ns.number: (idx + 1, ns) for idx, ns in enumerate(ranked)}

    print("=== THỨ HẠNG CỦA 6 CON SỐ MỤC TIÊU TRONG TỔNG SỐ 55 SỐ ===")
    target_ranks = []
    for num in target_numbers:
        rank_idx, ns = rankings_map[num]
        target_ranks.append(rank_idx)
        gap = stats.recency.get('gaps', {}).get(num, 0)
        freq = stats.frequency.get('counts', {}).get(num, 0)
        r5 = stats.frequency.get('recent_5_counts', {}).get(num, 0)
        print(f"Số {num:2d} | Hạng: #{rank_idx:2d}/55 | Score: {ns.final_model_score:.2f} | Tần suất: {freq}/{len(draws)} | Gần đây (5 kỳ): {r5} lần | Khoảng cách vắng mặt (Gap): {gap}")

    print("\nTop 15 số điểm cao nhất của hệ thống tại thời điểm 01/10/2026:")
    top_15_nums = [ns.number for ns in ranked[:15]]
    print(top_15_nums)
    matches_in_top15 = set(target_numbers) & set(top_15_nums)
    print(f"Số con trúng trong Top 15 số điểm cao nhất: {len(matches_in_top15)} số -> {sorted(list(matches_in_top15))}")

    # Top 20
    top_20_nums = [ns.number for ns in ranked[:20]]
    matches_in_top20 = set(target_numbers) & set(top_20_nums)
    print(f"Số con trúng trong Top 20: {len(matches_in_top20)} số -> {sorted(list(matches_in_top20))}")

    # 3. Kiểm tra 15 Vé do CombinationGenerator sinh ra
    print("\n=== KIỂM TRA 15 VÉ SIÊU TUYỂN CHỌN SINH RA TỪ TOOL ===")
    combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
    combos = combo_gen.generate(scores, num_per_strategy=3)

    best_match = 0
    best_ticket = None
    best_strategy = ""

    for idx, c in enumerate(combos, 1):
        matched = set(c.numbers) & set(target_numbers)
        match_count = len(matched)
        if match_count > best_match:
            best_match = match_count
            best_ticket = c.numbers
            best_strategy = c.strategy
        print(f"Vé #{idx:2d} ({c.strategy}): {c.numbers} | Trùng: {match_count} số {sorted(list(matched)) if matched else ''}")

    print(f"\nKết quả tốt nhất trong 15 vé: Trúng {best_match} số ({sorted(list(set(best_ticket) & set(target_numbers)))}) thuộc chiến lược '{best_strategy}'")

    # 4. Kiểm tra Ma trận Wheeling và Custom Pool
    print("\n=== KIỂM TRA MA TRẬN WHEELING SYSTEM ===")
    for wheel_size in [10, 12, 14, 16, 18]:
        wheel_pool = [ns.number for ns in ranked[:wheel_size]]
        pool_matches = set(target_numbers) & set(wheel_pool)
        print(f"Wheel {wheel_size} số (Top {wheel_size} Model Score): Chứa {len(pool_matches)}/{len(target_numbers)} số trúng -> {sorted(list(pool_matches))}")

    db.close()

if __name__ == '__main__':
    run_backtest()
