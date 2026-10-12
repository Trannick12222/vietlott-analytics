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

def test_draw_1407():
    db = SessionLocal()
    # Lấy các kỳ đến kỳ 1406 (2026-10-03)
    draws = db.query(Draw).filter(
        Draw.lottery_type == LotteryType.POWER_655,
        Draw.draw_number < 1407
    ).order_by(Draw.draw_date.asc()).all()

    target = [6, 7, 18, 20, 24, 27]
    print(f"Tổng số kỳ trước kỳ 1407: {len(draws)} kỳ")
    print(f"Kỳ mới nhất trước đó: Kỳ {draws[-1].draw_number} ({draws[-1].draw_date}) -> {[draws[-1].number_1, draws[-1].number_2, draws[-1].number_3, draws[-1].number_4, draws[-1].number_5, draws[-1].number_6]}")
    print(f"Bộ số thực tế kỳ 1407 (06/10/2026): {target}")
    print(f"Tổng thực tế: {sum(target)}, Max thực tế: {max(target)}, Min: {min(target)}\n")

    service = AnalyticsService(db)
    draw_lists = service._draws_to_number_lists(draws)
    config = LOTTERY_CONFIGS[LotteryType.POWER_655]

    stats = analyze_all(draw_lists, lottery_type="power", decay_factor=settings.DECAY_FACTOR)
    raw = service._build_raw_scores(stats, config)

    mc = MonteCarloSimulator(config.max_number, config.numbers_per_draw)
    raw['monte_carlo'] = mc.run_simulation(100000).number_probabilities

    scoring = EnsembleScoringEngine(config.max_number)
    scores = scoring.calculate_ensemble_scores(raw)
    ranked = sorted(scores.values(), key=lambda x: x.final_model_score, reverse=True)
    rankings_map = {ns.number: (idx + 1, ns) for idx, ns in enumerate(ranked)}

    print("=== THỨ HẠNG CỦA 6 SỐ KỲ 1407 TRONG 55 SỐ ===")
    for num in target:
        r, ns = rankings_map[num]
        gap = stats.recency.get('gaps', {}).get(num, 0)
        freq = stats.frequency.get('counts', {}).get(num, 0)
        print(f"Số {num:2d} | Hạng: #{r:2d}/55 | Score: {ns.final_model_score:.2f} | Gap: {gap} kỳ | Tần suất: {freq}/{len(draws)}")

    # Dự báo nhịp
    regime_data = getattr(stats, 'regime', {})
    regime_analysis = regime_data.get('regime_analysis', {}) if isinstance(regime_data, dict) else {}
    forecast = regime_analysis.get('next_draw_forecast', {})
    print("\n=== DỰ BÁO NHỊP CỦA TOOL TRƯỚC KỲ 1407 ===")
    print("Dự báo nhịp:", forecast.get('predicted_regime'))
    print("Xác suất các nhịp:", forecast.get('probabilities'))
    print("Min range:", forecast.get('expected_min_range'))
    print("Max range:", forecast.get('expected_max_range'))
    print("Sum range:", forecast.get('expected_sum_range'))

    # Sinh 15 vé
    combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
    combos = combo_gen.generate(scores, num_per_strategy=3)
    print("\n=== 15 VÉ TOOL SINH RA ===")
    for idx, c in enumerate(combos, 1):
        matched = set(c.numbers) & set(target)
        print(f"Vé #{idx:2d} ({c.strategy:38s}): {c.numbers} | Trùng {len(matched)} số {list(matched) if matched else ''}")

    db.close()

if __name__ == '__main__':
    test_draw_1407()
