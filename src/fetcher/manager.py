import logging
from typing import List, Tuple
from datetime import datetime
from src.database.repository import DatabaseRepository
from src.database.models import FetchLog
from src.config.settings import LotteryType
from src.fetcher.vietlott_source import VietlottOfficialSource
from src.fetcher.backup_source import BackupSource
from src.fetcher.manual_source import ManualSource
from src.validation.validator import validate_draw_data

logger = logging.getLogger(__name__)

class FetchManager:
    """Manages the fetching process, orchestrating sources, validation and persistence."""
    
    def __init__(self, db_repo: DatabaseRepository, data_dir: str = "data"):
        self.db_repo = db_repo
        self.sources = [
            VietlottOfficialSource(),
            BackupSource(),
            ManualSource(data_dir=data_dir)
        ]
        
    def sync_latest(self, lottery_type: LotteryType, limit: int = 20) -> Tuple[int, str]:
        """
        Attempt to fetch and sync the latest draws using available sources.
        Returns (number_of_records_added, source_used).
        """
        for source in self.sources:
            try:
                logger.info(f"Attempting to fetch from {source.name} for {lottery_type}")
                raw_data = source.fetch_latest(lottery_type, limit)
                
                if not raw_data:
                    logger.warning(f"No data returned from {source.name}")
                    continue
                    
                # Validate data
                valid_data = []
                for data in raw_data:
                    is_valid, error = validate_draw_data(data)
                    if is_valid:
                        valid_data.append(data)
                    else:
                        logger.error(f"Validation error for draw {data.get('draw_number')}: {error}")
                
                if not valid_data:
                    logger.warning(f"No valid data obtained from {source.name}")
                    continue
                    
                # Convert to models and persist
                models = source.to_models(valid_data)
                added_count = self.db_repo.insert_draws_bulk(models)
                
                # Log success
                self._log_fetch(lottery_type, source.name, True, added_count)
                return added_count, source.name
                
            except Exception as e:
                logger.error(f"Error syncing from {source.name}: {e}")
                self._log_fetch(lottery_type, source.name, False, 0, str(e))
                
        return 0, "none"
        
    def _log_fetch(self, lottery_type: LotteryType, source: str, success: bool, records: int, error: str = None):
        log = FetchLog(
            lottery_type=lottery_type,
            source=source,
            success=success,
            records_added=records,
            error_message=error
        )
        self.db_repo.log_fetch(log)
