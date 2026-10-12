from typing import List, Dict, Any, Tuple

def analyze_consecutive(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform analysis of consecutive numbers in draws.
    """
    if not draws:
        return {}

    pairs_freq: Dict[Tuple[int, int], int] = {}
    triples_freq: Dict[Tuple[int, int, int], int] = {}
    
    pairs_per_draw = []
    triples_per_draw = []
    
    total_consecutive_pairs = 0
    
    for draw in draws:
        sorted_draw = sorted(draw)
        draw_pairs = []
        draw_triples = []
        
        # Find pairs
        for i in range(len(sorted_draw) - 1):
            if sorted_draw[i+1] - sorted_draw[i] == 1:
                pair = (sorted_draw[i], sorted_draw[i+1])
                draw_pairs.append(pair)
                pairs_freq[pair] = pairs_freq.get(pair, 0) + 1
                total_consecutive_pairs += 1
                
        # Find triples
        for i in range(len(sorted_draw) - 2):
            if sorted_draw[i+1] - sorted_draw[i] == 1 and sorted_draw[i+2] - sorted_draw[i+1] == 1:
                triple = (sorted_draw[i], sorted_draw[i+1], sorted_draw[i+2])
                draw_triples.append(triple)
                triples_freq[triple] = triples_freq.get(triple, 0) + 1
                
        pairs_per_draw.append(draw_pairs)
        triples_per_draw.append(draw_triples)
        
    avg_pairs = total_consecutive_pairs / len(draws) if draws else 0.0
    
    return {
        "pairs_per_draw": pairs_per_draw,
        "triples_per_draw": triples_per_draw,
        "pairs_frequency": {str(k): v for k, v in sorted(pairs_freq.items(), key=lambda item: item[1], reverse=True)},
        "triples_frequency": {str(k): v for k, v in sorted(triples_freq.items(), key=lambda item: item[1], reverse=True)},
        "avg_pairs_per_draw": avg_pairs
    }
