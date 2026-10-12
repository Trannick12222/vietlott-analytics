import os
from enum import Enum
from pathlib import Path
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class LotteryType(str, Enum):
    MEGA_645 = "MEGA_645"
    POWER_655 = "POWER_655"

@dataclass
class LotteryConfig:
    max_number: int
    numbers_per_draw: int
    stat_type: str  # "mega" or "power" for statistics engine
    baseline_probability: float
    low_high_boundary: int
    buckets: list

LOTTERY_CONFIGS = {
    LotteryType.MEGA_645: LotteryConfig(
        max_number=45, numbers_per_draw=6, stat_type="mega",
        baseline_probability=6/45, low_high_boundary=22,
        buckets=[(1,9),(10,18),(19,27),(28,36),(37,45)]
    ),
    LotteryType.POWER_655: LotteryConfig(
        max_number=55, numbers_per_draw=6, stat_type="power",
        baseline_probability=6/55, low_high_boundary=27,
        buckets=[(1,11),(12,22),(23,33),(34,44),(45,55)]
    ),
}

# Keep Settings class for env vars
class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'vietlott.db'}")
    MONTE_CARLO_SIMULATIONS: int = int(os.getenv("MONTE_CARLO_SIMULATIONS", "100000"))
    DECAY_FACTOR: float = float(os.getenv("DECAY_FACTOR", "0.05"))
    DATA_DIR: str = os.getenv("DATA_DIR", str(BASE_DIR / "data"))

settings = Settings()
