import logging
import httpx
from typing import List, Dict, Any
from src.fetcher.base import DataSource
from src.config.settings import LotteryType

logger = logging.getLogger(__name__)

class BackupSource(DataSource):
    """Backup data source scraping from secondary lottery portals."""
    
    @property
    def name(self) -> str:
        return "backup_scraper"
        
    def fetch_latest(self, lottery_type: LotteryType, limit: int = 10) -> List[Dict[str, Any]]:
        logger.info(f"Attempting to fetch from backup source for {lottery_type}")
        # Placeholder for secondary online source adapter
        # If unavailable, gracefully returns empty list to trigger manual_source
        return []

    def fetch_by_range(self, lottery_type: LotteryType, start_draw: int, end_draw: int) -> List[Dict[str, Any]]:
        return []
