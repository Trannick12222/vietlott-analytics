import pytest
from src.config.settings import LotteryType
from src.database.repository import DatabaseRepository
from src.database.models import Draw
from src.api.service import AnalyticsService

def test_backtesting_insufficient_data(db_session):
    repo = DatabaseRepository(db_session)
    service = AnalyticsService(db_session)
    result = service.get_backtest_results(LotteryType.MEGA_645)
    assert result["status"] == "insufficient_data"

def test_backtesting_with_draws(db_session):
    repo = DatabaseRepository(db_session)
    import datetime
    for i in range(1, 26):
        draw = Draw(
            lottery_type=LotteryType.MEGA_645,
            draw_number=1000 + i,
            draw_date=datetime.date(2024, 1, 1) + datetime.timedelta(days=i),
            number_1=1,
            number_2=10,
            number_3=20,
            number_4=30,
            number_5=40,
            number_6=45,
            source="test"
        )
        repo.insert_draw(draw)
        
    service = AnalyticsService(db_session)
    result = service.get_backtest_results(LotteryType.MEGA_645)
    assert result["status"] == "completed"
    assert "model" in result
    assert "random_baseline" in result
    assert "better_than_random" in result
    assert "disclaimer" in result
