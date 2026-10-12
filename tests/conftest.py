import pytest
import random

@pytest.fixture
def sample_mega_draws():
    """Returns 20 sample Mega 6/45 draws."""
    return [
        sorted(random.sample(range(1, 46), 6))
        for _ in range(20)
    ]

@pytest.fixture
def sample_power_draws():
    """Returns 20 sample Power 6/55 draws."""
    return [
        sorted(random.sample(range(1, 56), 6))
        for _ in range(20)
    ]

@pytest.fixture
def db_session():
    """In-memory SQLite session for testing."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from src.database.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
