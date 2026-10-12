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

def test_draw_1409():
    db = SessionLocal()
    draws = db.query(Draw).filter(
        Draw.lottery_type == LotteryType.POWER_655,
        Draw.draw_number < 1409
    ).order_by(Draw.draw_date.asc()).all()

    target = [14, 17, 21, 23, 24, 39]
    print(f"Tổng số kỳ trước kỳ 1409: {len(draws)} kỳ")
    print(f"Bộ số thực tế kỳ 1409 (10/10/2026): {target}")
    print(f"Tổng: {sum(target)}, Max: {max(target)}, Min: {min(target)}")

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

    print("\n=== THỨ HẠNG CỦA 6 SỐ KỲ 1409 TRONG 55 SỐ ===")
    for n in target:
        r, ns = rankings_map[n]
        gap = stats.recency.get('gaps', {}).get(n, 0)
        freq = stats.frequency.get('counts', {}).get(n, 0)
        print(f"Số {n:2d} | Hạng: #{r:2d}/55 | Score: {ns.final_model_score:.2f} | Gap: {gap:2d} kỳ | Tần suất: {freq:2d}")

    # Kiểm tra Ma Trận Wheeling Low Comp
    wheel = WheelingEngine(config.max_number)
    w_low = wheel.generate_wheel(scores, wheel_size=12, strategy='low_comp')
    print("\n=== WHEEL 12 LOW COMP (NÉN DẢI THẤP) ===")
    print("Pool số:", w_low.selected_numbers)
    matches = set(w_low.selected_numbers) & set(target)
    print(f"Trúng trong pool: {len(matches)} số -> {sorted(list(matches))}")
    for i, t in enumerate(w_low.tickets, 1):
        hit = set(t) & set(target)
        hit_str = str(sorted(list(hit))) if hit else ""
        print(f"Vé #{i}: {t} | Trùng: {len(hit)} {hit_str}")

    # Kiểm tra 15 vé của CombinationGenerator
    combo_gen = CombinationGenerator(config.max_number, config.numbers_per_draw)
    combos = combo_gen.generate(scores, num_per_strategy=3)
    print("\n=== 15 VÉ TỔ HỢP CỦA TOOL ===")
    for idx, c in enumerate(combos, 1):
        hit = set(c.numbers) & set(target)
        hit_str = str(sorted(list(hit))) if hit else ""
        print(f"Vé #{idx:2d} ({c.strategy:38s}): {c.numbers} | Trùng: {len(hit)} {hit_str}")

    db.close()

if __name__ == '__main__':
    test_draw_1409()
