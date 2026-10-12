import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.connection import SessionLocal
from src.database.models import Draw
from src.config.settings import LotteryType, LOTTERY_CONFIGS, settings
from src.statistics.engine import analyze_all
from src.prediction.scoring import EnsembleScoringEngine
from src.prediction.combination import CombinationGenerator
from src.prediction.wheeling import WheelingEngine
from src.simulation.monte_carlo import MonteCarloSimulator
from src.api.service import AnalyticsService

def run_backtest():
    db = SessionLocal()
    # Lấy các kỳ đến ngày 2026-10-04 (kỳ 1571)
    draws = db.query(Draw).filter(
        Draw.lottery_type == LotteryType.MEGA_645,
        Draw.draw_date <= '2026-10-04'
    ).order_by(Draw.draw_date.asc()).all()

    target_numbers = [10, 14, 36, 37, 41, 43]
    print(f"Tổng số kỳ phân tích (<= 2026-10-04): {len(draws)} kỳ")
    print(f"Kỳ mới nhất trong tập dữ liệu: Kỳ {draws[-1].draw_number} ({draws[-1].draw_date}) với kết quả {[draws[-1].number_1, draws[-1].number_2, draws[-1].number_3, draws[-1].number_4, draws[-1].number_5, draws[-1].number_6]}")
    print(f"Bộ số mục tiêu cần dự đoán (kỳ 1572 ngày 07/10/2026): {target_numbers}\n")

    service = AnalyticsService(db)
    draw_lists = service._draws_to_number_lists(draws)
    config = LOTTERY_CONFIGS[LotteryType.MEGA_645]

    # 1. Thống kê toàn diện 21 công thức
    stats = analyze_all(draw_lists, lottery_type="mega", decay_factor=settings.DECAY_FACTOR)
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

    print("=== THỨ HẠNG CỦA 6 CON SỐ MỤC TIÊU TRONG TỔNG SỐ 45 SỐ ===")
    target_ranks = []
    for num in target_numbers:
        rank_idx, ns = rankings_map[num]
        target_ranks.append(rank_idx)
        gap = stats.recency.get('gaps', {}).get(num, 0)
        freq = stats.frequency.get('counts', {}).get(num, 0)
        r5 = stats.frequency.get('recent_5_counts', {}).get(num, 0)
        regime_sc = getattr(ns, 'regime_score', 50.0)
        print(f"Số {num:2d} | Hạng: #{rank_idx:2d}/45 | Score: {ns.final_model_score:.2f} | Tần suất: {freq}/{len(draws)} | Gần đây (5 kỳ): {r5} lần | Gap: {gap} kỳ | Regime Score: {regime_sc:.1f}")

    print("\nTop 12 số điểm cao nhất của hệ thống tại thời điểm 04/10/2026:")
    top_12_nums = [ns.number for ns in ranked[:12]]
    print(top_12_nums)
    matches_in_top12 = set(target_numbers) & set(top_12_nums)
    print(f"Số con trúng trong Top 12 số Model Score: {len(matches_in_top12)} số -> {sorted(list(matches_in_top12))}")

    top_15_nums = [ns.number for ns in ranked[:15]]
    matches_in_top15 = set(target_numbers) & set(top_15_nums)
    print(f"Số con trúng trong Top 15 số Model Score: {len(matches_in_top15)} số -> {sorted(list(matches_in_top15))}")

    # 3. Phân tích dự báo nhịp (Regime Forecast) cho kỳ 07/10/2026
    regime_data = getattr(stats, 'regime', {})
    regime_analysis = regime_data.get('regime_analysis', {}) if isinstance(regime_data, dict) else {}
    forecast = regime_analysis.get('next_draw_forecast', {})
    print("\n=== DỰ BÁO NHỊP CỰC TRỊ & MARKOV CHO KỲ TIẾP THEO (07/10/2026) ===")
    print("Dự báo nhịp:", forecast.get('predicted_regime'))
    print("Xác suất 3 nhịp:", forecast.get('probabilities'))
    print("Khoảng Min kỳ vọng:", forecast.get('expected_min_range'))
    print("Khoảng Max kỳ vọng:", forecast.get('expected_max_range'))
    print("Khoảng Tổng kỳ vọng:", forecast.get('expected_sum_range'))

    # 4. Kiểm tra 15 Vé Siêu Tuyển Chọn
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

    # 5. Kiểm tra Ma Trận Wheeling System
    print("\n=== KIỂM TRA MA TRẬN WHEELING SYSTEM ===")
    wheel_engine = WheelingEngine(config.max_number)
    for strat in ['balanced', 'cold_outbreak', 'low_comp', 'elite']:
        for size in [10, 12, 14]:
            w_res = wheel_engine.generate_wheel(scores, wheel_size=size, strategy=strat)
            pool_matches = set(target_numbers) & set(w_res.selected_numbers)
            
            # Đếm số vé trúng
            ticket_hits = [len(set(t) & set(target_numbers)) for t in w_res.tickets]
            max_ticket_hit = max(ticket_hits) if ticket_hits else 0
            count_win_3plus = sum(1 for h in ticket_hits if h >= 3)
            
            print(f"Wheel {size} ({strat:13s}): Dàn pool trúng {len(pool_matches)}/{len(target_numbers)} số {sorted(list(pool_matches))} | Vé trúng cao nhất: {max_ticket_hit} số | Số vé trúng giải (>=3 số): {count_win_3plus}/{len(w_res.tickets)}")

    db.close()

if __name__ == '__main__':
    run_backtest()
