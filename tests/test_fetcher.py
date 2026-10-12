import pytest
from src.config.settings import LotteryType
from src.database.repository import DatabaseRepository
from src.fetcher.vietlott_source import VietlottOfficialSource
from src.fetcher.backup_source import BackupSource
from src.fetcher.manual_source import ManualSource
from src.fetcher.manager import FetchManager

def test_vietlott_official_source():
    source = VietlottOfficialSource()
    assert source.name == "vietlott_official"
    res = source.fetch_latest(LotteryType.MEGA_645, limit=5)
    assert isinstance(res, list)

def test_backup_source():
    source = BackupSource()
    assert source.name == "backup_scraper"
    res = source.fetch_latest(LotteryType.MEGA_645, limit=5)
    assert isinstance(res, list)

def test_manual_source():
    source = ManualSource(data_dir="data")
    assert source.name == "manual_csv"
    res = source.fetch_latest(LotteryType.MEGA_645, limit=5)
    assert len(res) == 5
    first = res[0]
    assert "draw_number" in first
    assert len(first["numbers"]) == 6
    assert first["numbers"] == sorted(first["numbers"])

def test_fetch_manager_fallback_and_db(db_session):
    repo = DatabaseRepository(db_session)
    manager = FetchManager(repo, data_dir="data")
    
    # First sync should add records (either from live official source or manual fallback)
    added, source_name = manager.sync_latest(LotteryType.MEGA_645, limit=10)
    assert added == 10
    assert source_name in ["vietlott_official", "manual_csv"]
    
    # Second sync of the same draws should prevent duplicates
    added_second, _ = manager.sync_latest(LotteryType.MEGA_645, limit=10)
    assert added_second == 0
