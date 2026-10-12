from datetime import datetime
from sqlalchemy import Column, Integer, String, Date, DateTime, Float, Enum, UniqueConstraint, Boolean
from sqlalchemy.ext.declarative import declarative_base
from src.config.settings import LotteryType

Base = declarative_base()

class Draw(Base):
    __tablename__ = 'draws'

    id = Column(Integer, primary_key=True, index=True)
    lottery_type = Column(Enum(LotteryType), nullable=False, index=True)
    draw_number = Column(Integer, nullable=False, index=True)
    draw_date = Column(Date, nullable=False, index=True)
    
    # Main numbers sorted ascending
    number_1 = Column(Integer, nullable=False)
    number_2 = Column(Integer, nullable=False)
    number_3 = Column(Integer, nullable=False)
    number_4 = Column(Integer, nullable=False)
    number_5 = Column(Integer, nullable=False)
    number_6 = Column(Integer, nullable=False)
    
    # Optional power ball/jackpot 2 (used for Power 6/55)
    jackpot_2 = Column(Integer, nullable=True)
    
    source = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint('lottery_type', 'draw_number', name='uq_lottery_draw'),
    )

    def __repr__(self):
        return f"<Draw(lottery_type={self.lottery_type}, draw_number={self.draw_number}, date={self.draw_date})>"

class FetchLog(Base):
    __tablename__ = 'fetch_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    lottery_type = Column(Enum(LotteryType), nullable=False)
    fetch_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String, nullable=False)
    success = Column(Boolean, nullable=False)
    records_added = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
