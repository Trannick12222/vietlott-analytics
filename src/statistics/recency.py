from typing import List, Dict, Any, Tuple

def _get_max_num(lottery_type: str) -> int:
    return 45 if lottery_type.lower() == "mega" else 55

def analyze_recency(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform recency analysis on lottery draws.
    
    Note: Statistical independence means that 'overdue' numbers are mathematically 
    no more likely to appear in the next draw than any other number.
    """
    max_num = _get_max_num(lottery_type)
    if not draws:
        return {"gaps": {}, "hot": [], "cold": [], "overdue": []}

    gaps = {i: -1 for i in range(1, max_num + 1)}
    
    # Iterate backwards to find the most recent appearance
    for i, draw in enumerate(reversed(draws)):
        for num in draw:
            if 1 <= num <= max_num and gaps[num] == -1:
                gaps[num] = i
                
    # If a number never appeared, its gap is the total number of draws
    total_draws = len(draws)
    for num in gaps:
        if gaps[num] == -1:
            gaps[num] = total_draws

    # Define thresholds
    # Hot: appeared in the last 3 draws
    # Cold: hasn't appeared in the last 15 draws
    # Overdue: hasn't appeared in the last 20 draws (Reminder: this does not mean it is 'due' to appear)
    
    hot = [num for num, gap in gaps.items() if gap <= 3]
    cold = [num for num, gap in gaps.items() if gap >= 15]
    overdue = [num for num, gap in gaps.items() if gap >= 20]
    
    # Sort by gap length (descending for overdue/cold, ascending for hot)
    hot.sort(key=lambda x: gaps[x])
    cold.sort(key=lambda x: gaps[x], reverse=True)
    overdue.sort(key=lambda x: gaps[x], reverse=True)

    return {
        "gaps": gaps,
        "hot": hot,
        "cold": cold,
        "overdue": overdue
    }
