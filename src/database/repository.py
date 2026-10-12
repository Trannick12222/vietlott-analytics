import logging
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from src.database.models import Draw, FetchLog
from src.config.settings import LotteryType

logger = logging.getLogger(__name__)

class DatabaseRepository:
    def __init__(self, session: Session):
        self.session = session
        
    def get_latest_draws(self, lottery_type: LotteryType, limit: int = 100) -> List[Draw]:
        return self.session.query(Draw)\
            .filter(Draw.lottery_type == lottery_type)\
            .order_by(Draw.draw_date.desc(), Draw.draw_number.desc())\
            .limit(limit)\
            .all()
            
    def get_draws_by_date_range(self, lottery_type: LotteryType, start_date: date, end_date: date) -> List[Draw]:
        return self.session.query(Draw)\
            .filter(Draw.lottery_type == lottery_type)\
            .filter(Draw.draw_date >= start_date)\
            .filter(Draw.draw_date <= end_date)\
            .order_by(Draw.draw_date.asc())\
            .all()
            
    def get_all_draws(self, lottery_type: LotteryType) -> List[Draw]:
        return self.session.query(Draw)\
            .filter(Draw.lottery_type == lottery_type)\
            .order_by(Draw.draw_date.asc(), Draw.draw_number.asc())\
            .all()
            
    def get_draw_by_number(self, lottery_type: LotteryType, draw_number: int) -> Optional[Draw]:
        return self.session.query(Draw)\
            .filter(Draw.lottery_type == lottery_type)\
            .filter(Draw.draw_number == draw_number)\
            .first()

    def insert_draw(self, draw: Draw) -> bool:
        try:
            # Check if it exists
            existing = self.get_draw_by_number(draw.lottery_type, draw.draw_number)
            if existing:
                return False
                
            self.session.add(draw)
            self.session.commit()
            return True
        except IntegrityError:
            self.session.rollback()
            logger.warning(f"Draw {draw.draw_number} for {draw.lottery_type} already exists.")
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error inserting draw: {e}")
            raise
            
    def insert_draws_bulk(self, draws: List[Draw]) -> int:
        added_count = 0
        for draw in draws:
            if self.insert_draw(draw):
                added_count += 1
        return added_count
        
    def log_fetch(self, log: FetchLog):
        self.session.add(log)
        self.session.commit()

def init_db(engine):
    from src.database.models import Base
    Base.metadata.create_all(bind=engine)
