import logging
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path
from src.fetcher.base import DataSource
from src.config.settings import LotteryType

logger = logging.getLogger(__name__)

class ManualSource(DataSource):
    """Data source reading from local CSV files."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        
    @property
    def name(self) -> str:
        return "manual_csv"
        
    def _get_file_path(self, lottery_type: LotteryType) -> Path:
        filename = "sample_mega645.csv" if lottery_type == LotteryType.MEGA_645 else "sample_power655.csv"
        return self.data_dir / filename
        
    def fetch_latest(self, lottery_type: LotteryType, limit: int = 10) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(lottery_type)
        if not file_path.exists():
            logger.error(f"Sample data file not found: {file_path}")
            return []
            
        try:
            df = pd.read_csv(file_path)
            # Sort by draw_date descending and take top N
            df['draw_date'] = pd.to_datetime(df['draw_date']).dt.date
            df = df.sort_values(['draw_date', 'draw_number'], ascending=[False, False]).head(limit)
            return self._df_to_dicts(df, lottery_type)
        except Exception as e:
            logger.error(f"Error reading CSV {file_path}: {e}")
            return []

    def fetch_by_range(self, lottery_type: LotteryType, start_draw: int, end_draw: int) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(lottery_type)
        if not file_path.exists():
            return []
            
        try:
            df = pd.read_csv(file_path)
            df['draw_date'] = pd.to_datetime(df['draw_date']).dt.date
            mask = (df['draw_number'] >= start_draw) & (df['draw_number'] <= end_draw)
            filtered_df = df.loc[mask].sort_values(['draw_date', 'draw_number'], ascending=[False, False])
            return self._df_to_dicts(filtered_df, lottery_type)
        except Exception as e:
            logger.error(f"Error filtering CSV {file_path}: {e}")
            return []
            
    def _df_to_dicts(self, df: pd.DataFrame, lottery_type: LotteryType) -> List[Dict[str, Any]]:
        results = []
        for _, row in df.iterrows():
            numbers = [int(row[f'num{i}']) for i in range(1, 7)]
            jackpot_2 = int(row['jackpot_2']) if 'jackpot_2' in row and pd.notna(row['jackpot_2']) else None
            
            results.append({
                'lottery_type': lottery_type,
                'draw_number': int(row['draw_number']),
                'draw_date': row['draw_date'],
                'numbers': sorted(numbers),
                'jackpot_2': jackpot_2
            })
        return results
