import pytest
from src.validation.validator import validate_draw, ValidationError

def test_valid_mega645_draw():
    draw = [5, 12, 18, 25, 33, 40]
    assert validate_draw(draw, game_type="mega") is True

def test_valid_power655_draw():
    draw = [10, 20, 30, 40, 50, 55]
    assert validate_draw(draw, game_type="power") is True

def test_missing_fields():
    with pytest.raises(ValidationError):
        validate_draw(None, game_type="mega")

def test_wrong_number_count():
    draw = [1, 2, 3, 4, 5] # Only 5 numbers
    with pytest.raises(ValidationError):
        validate_draw(draw, game_type="mega")

def test_out_of_range_numbers():
    draw = [1, 2, 3, 4, 5, 46] # 46 is out of range for mega
    with pytest.raises(ValidationError):
        validate_draw(draw, game_type="mega")

def test_duplicate_numbers():
    draw = [1, 2, 3, 4, 5, 5]
    with pytest.raises(ValidationError):
        validate_draw(draw, game_type="mega")

def test_unsorted_numbers():
    draw = [5, 4, 3, 2, 1, 6]
    with pytest.raises(ValidationError):
        validate_draw(draw, game_type="mega")

def test_invalid_draw_number():
    with pytest.raises(ValidationError):
        validate_draw([1,2,3,4,5,6], game_type="mega", draw_id=-1)

def test_invalid_date():
    with pytest.raises(ValidationError):
        validate_draw([1,2,3,4,5,6], game_type="mega", date="invalid-date")
