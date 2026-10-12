import logging
from typing import Dict, Any, Tuple
from datetime import date, datetime

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception raised when lottery draw validation fails."""
    pass


def validate_draw_data(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate a single draw data dict."""
    # Check required fields
    required = ['lottery_type', 'draw_number', 'draw_date', 'numbers']
    for field in required:
        if field not in data or data[field] is None:
            return False, f"Missing required field: {field}"
    
    numbers = data['numbers']
    lottery_type = str(data['lottery_type'])
    
    if not isinstance(numbers, list):
        return False, "Numbers must be a list"

    # Check exactly 6 numbers
    if len(numbers) != 6:
        return False, f"Expected 6 numbers, got {len(numbers)}"
    
    # Determine valid range
    if 'MEGA' in lottery_type.upper() or '645' in lottery_type or lottery_type.lower() == 'mega':
        max_num = 45
    else:
        max_num = 55
    
    # Check range
    for n in numbers:
        if not isinstance(n, int) or n < 1 or n > max_num:
            return False, f"Number {n} out of range [1, {max_num}]"
    
    # Check no duplicates
    if len(set(numbers)) != 6:
        return False, "Duplicate numbers found"
    
    # Check sorted ascending
    if numbers != sorted(numbers):
        return False, "Numbers not sorted ascending"
    
    # Validate draw_number
    draw_number = data['draw_number']
    if not isinstance(draw_number, int) or draw_number <= 0:
        return False, f"Invalid draw number: {draw_number}"
    
    # Validate date
    draw_date = data['draw_date']
    if isinstance(draw_date, str):
        try:
            datetime.strptime(draw_date, "%Y-%m-%d")
        except ValueError:
            return False, f"Invalid date format: {draw_date}"
    elif not isinstance(draw_date, (date, datetime)):
        return False, f"Invalid date type: {type(draw_date)}"
    
    return True, "Valid"


def validate_draw(numbers: Any, game_type: str = "mega", draw_id: int = 1, date: Any = "2024-01-01") -> bool:
    """Validate a draw, raising ValidationError if invalid."""
    if numbers is None:
        raise ValidationError("Draw numbers cannot be None")
        
    data = {
        "lottery_type": game_type,
        "draw_number": draw_id,
        "draw_date": date,
        "numbers": numbers
    }
    is_valid, msg = validate_draw_data(data)
    if not is_valid:
        raise ValidationError(msg)
    return True

