import pandas as pd
import numpy as np
from typing import List, Dict, Any

def _get_max_num(lottery_type: str) -> int:
    return 45 if lottery_type.lower() == "mega" else 55

def analyze_frequency(draws: List[List[int]], lottery_type: str = "mega", decay_factor: float = 0.05) -> Dict[str, Any]:
    """
    Perform frequency analysis on lottery draws.
    
    Calculates:
    - Overall frequency and percentage
    - Recent frequency (last 5, 10 draws)
    - Weighted frequency based on recency
    """
    max_num = _get_max_num(lottery_type)
    if not draws:
        return {
            "counts": {}, "frequency_pct": {}, 
            "recent_5_counts": {}, "recent_10_counts": {},
            "weighted_frequency": {}
        }

    total_draws = len(draws)
    
    counts = {i: 0 for i in range(1, max_num + 1)}
    for draw in draws:
        for num in draw:
            if 1 <= num <= max_num:
                counts[num] += 1
            
    frequency_pct = {k: (v / total_draws) * 100 for k, v in counts.items()}
    
    recent_5 = draws[-5:] if len(draws) >= 5 else draws
    recent_10 = draws[-10:] if len(draws) >= 10 else draws
    
    counts_5 = {i: 0 for i in range(1, max_num + 1)}
    for draw in recent_5:
        for num in draw:
            if 1 <= num <= max_num:
                counts_5[num] += 1
                
    counts_10 = {i: 0 for i in range(1, max_num + 1)}
    for draw in recent_10:
        for num in draw:
            if 1 <= num <= max_num:
                counts_10[num] += 1
                
    weighted_freq = {i: 0.0 for i in range(1, max_num + 1)}
    for i, draw in enumerate(reversed(draws)):
        weight = max(0.0, 1.0 - i * decay_factor)
        if weight <= 0:
            break
        for num in draw:
            if 1 <= num <= max_num:
                weighted_freq[num] += weight
                
    return {
        "counts": counts,
        "frequency_pct": frequency_pct,
        "recent_5_counts": counts_5,
        "recent_10_counts": counts_10,
        "weighted_frequency": weighted_freq
    }

def analyze_moving_window(draws: List[List[int]], window_sizes: List[int] = [5, 10, 20, 50, 100], lottery_type: str = "mega") -> Dict[int, Dict[int, List[int]]]:
    """
    Perform moving window frequency analysis to track how frequencies change over time.
    """
    max_num = _get_max_num(lottery_type)
    if not draws:
        return {}
        
    results = {}
    
    for w in window_sizes:
        if len(draws) < w:
            continue
            
        w_res = {i: [] for i in range(1, max_num + 1)}
        for i in range(len(draws) - w + 1):
            window_draws = draws[i:i+w]
            window_counts = {n: 0 for n in range(1, max_num + 1)}
            for draw in window_draws:
                for num in draw:
                    if 1 <= num <= max_num:
                        window_counts[num] += 1
            for n in range(1, max_num + 1):
                w_res[n].append(window_counts[n])
        results[w] = w_res
        
    return results
