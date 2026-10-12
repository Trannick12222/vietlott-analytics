import itertools
import numpy as np
from typing import List, Dict, Any

def analyze_correlation(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform correlation analysis to find pairs and triples that frequently appear together.
    WARNING: Correlation does not imply causation. In a truly random lottery, 
    frequent pairs are statistical noise and small sample sizes make these unreliable.
    """
    max_num = 45 if lottery_type.lower() == "mega" else 55
    if not draws:
        return {}

    pair_counts = {}
    triple_counts = {}
    
    # Co-occurrence matrix
    co_matrix = np.zeros((max_num + 1, max_num + 1), dtype=int)
    
    for draw in draws:
        sorted_draw = sorted(draw)
        
        # Pairs
        for pair in itertools.combinations(sorted_draw, 2):
            pair_counts[pair] = pair_counts.get(pair, 0) + 1
            co_matrix[pair[0], pair[1]] += 1
            co_matrix[pair[1], pair[0]] += 1
            
        # Triples
        for triple in itertools.combinations(sorted_draw, 3):
            triple_counts[triple] = triple_counts.get(triple, 0) + 1
            
    # Sort by frequency
    sorted_pairs = {str(k): v for k, v in sorted(pair_counts.items(), key=lambda item: item[1], reverse=True)}
    sorted_triples = {str(k): v for k, v in sorted(triple_counts.items(), key=lambda item: item[1], reverse=True)}
    
    return {
        "warning": "Small sample sizes make correlation unreliable. This does not predict future draws.",
        "top_pairs": dict(list(sorted_pairs.items())[:50]),  # Top 50 pairs
        "top_triples": dict(list(sorted_triples.items())[:50]), # Top 50 triples
        "co_matrix": co_matrix.tolist()
    }
