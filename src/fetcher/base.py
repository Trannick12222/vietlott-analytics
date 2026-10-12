from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.config.settings import LotteryType
from src.database.models import Draw

class DataSource(ABC):
    """Abstract base class for all Vietlott data sources."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the data source."""
        pass
        
    @abstractmethod
    def fetch_latest(self, lottery_type: LotteryType, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch the latest draws.
        Returns a list of dictionaries with raw draw data.
        """
        pass
        
    @abstractmethod
    def fetch_by_range(self, lottery_type: LotteryType, start_draw: int, end_draw: int) -> List[Dict[str, Any]]:
        """
        Fetch draws within a specific draw number range.
        Returns a list of dictionaries with raw draw data.
        """
        pass
        
    def to_models(self, raw_data: List[Dict[str, Any]]) -> List[Draw]:
        """Convert raw dictionary data to Draw models."""
        models = []
        for data in raw_data:
            draw = Draw(
                lottery_type=data['lottery_type'],
                draw_number=data['draw_number'],
                draw_date=data['draw_date'],
                number_1=data['numbers'][0],
                number_2=data['numbers'][1],
                number_3=data['numbers'][2],
                number_4=data['numbers'][3],
                number_5=data['numbers'][4],
                number_6=data['numbers'][5],
                jackpot_2=data.get('jackpot_2'),
                source=self.name
            )
            models.append(draw)
        return models
