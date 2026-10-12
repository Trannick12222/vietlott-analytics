import pytest
from src.prediction.combination import CombinationGenerator, generate_combinations, BaoCombination
from src.prediction.scoring import NumberScore

def test_valid_combination_generation():
    combinations = generate_combinations(n_combinations=5, game_type="mega")
    assert len(combinations) == 5

def test_combinations_have_6_unique_numbers():
    combinations = generate_combinations(n_combinations=1, game_type="mega")
    combo = combinations[0]
    assert len(combo) == 6
    assert len(set(combo)) == 6

def test_numbers_in_valid_range():
    combinations = generate_combinations(n_combinations=10, game_type="mega")
    for combo in combinations:
        assert all(1 <= num <= 45 for num in combo)

def test_odd_even_validation():
    combinations = generate_combinations(n_combinations=5, game_type="mega", filter_odd_even=True)
    for combo in combinations:
        odds = sum(1 for n in combo if n % 2 != 0)
        assert 0 < odds < 6

def test_all_strategies_generate_results():
    strategies = ["Hot", "Cold", "Balanced", "Statistical", "Random"]
    for strategy in strategies:
        combos = generate_combinations(n_combinations=1, game_type="mega", strategy=strategy)
        assert len(combos) == 1
        assert len(combos[0]) == 6

def test_generator_class_directly():
    gen = CombinationGenerator(max_number=45, numbers_per_draw=6)
    scores = {n: NumberScore(number=n, final_model_score=float(n)) for n in range(1, 46)}
    combos = gen.generate(scores, num_per_strategy=2)
    assert len(combos) == 10
    assert all(len(c.numbers) == 6 for c in combos)

def test_calculate_bao_tickets_and_cost():
    gen_mega = CombinationGenerator(max_number=45, numbers_per_draw=6)
    gen_power = CombinationGenerator(max_number=55, numbers_per_draw=6)

    # Bao 5
    assert gen_mega.calculate_bao_tickets(5) == 40
    assert gen_mega.calculate_bao_cost(5) == 400_000
    assert gen_power.calculate_bao_tickets(5) == 50
    assert gen_power.calculate_bao_cost(5) == 500_000

    # Bao 7: C(7, 6) = 7
    assert gen_mega.calculate_bao_tickets(7) == 7
    assert gen_mega.calculate_bao_cost(7) == 70_000

    # Bao 8: C(8, 6) = 28
    assert gen_mega.calculate_bao_tickets(8) == 28
    assert gen_mega.calculate_bao_cost(8) == 280_000

    # Bao 9: C(9, 6) = 84
    assert gen_mega.calculate_bao_tickets(9) == 84
    assert gen_mega.calculate_bao_cost(9) == 840_000

    # Bao 10: C(10, 6) = 210
    assert gen_mega.calculate_bao_tickets(10) == 210
    assert gen_mega.calculate_bao_cost(10) == 2_100_000

    # Bao 15: C(15, 6) = 5005
    assert gen_mega.calculate_bao_tickets(15) == 5005
    assert gen_mega.calculate_bao_cost(15) == 50_050_000

def test_generate_bao_combinations():
    gen = CombinationGenerator(max_number=45, numbers_per_draw=6)
    scores = {n: NumberScore(number=n, final_model_score=40.0 + (n % 20)) for n in range(1, 46)}

    for bao_type in [5, 7, 8, 9, 10, 12, 15]:
        combos = gen.generate_bao(scores, bao_type=bao_type, num_per_strategy=1)
        assert len(combos) == 5  # 5 comprehensive strategies
        for c in combos:
            assert isinstance(c, BaoCombination)
            assert len(c.numbers) == bao_type
            assert len(set(c.numbers)) == bao_type
            assert all(1 <= num <= 45 for num in c.numbers)
            assert c.numbers == sorted(c.numbers)
            assert c.cost == gen.calculate_bao_cost(bao_type)
            assert c.ticket_count == gen.calculate_bao_tickets(bao_type)

            d = c.to_dict()
            assert "strategy" in d
            assert "score" in d
            assert "odd_count" in d
            assert "even_count" in d
