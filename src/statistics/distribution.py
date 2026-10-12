from typing import List, Dict, Any

def analyze_distribution(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Perform distribution analysis (odd/even, high/low, buckets, sums).
    """
    if not draws:
        return {}

    is_mega = (lottery_type.lower() == "mega")
    max_num = 45 if is_mega else 55
    
    # High/Low threshold
    low_max = 22 if is_mega else 27
    
    # Buckets
    if is_mega:
        buckets = [(1,9), (10,18), (19,27), (28,36), (37,45)]
    else:
        buckets = [(1,11), (12,22), (23,33), (34,44), (45,55)]
        
    bucket_names = [f"{start}-{end}" for start, end in buckets]
    
    results = {
        "odd_even_per_draw": [],
        "odd_even_overall": {"odd": 0, "even": 0},
        "high_low_per_draw": [],
        "high_low_overall": {"high": 0, "low": 0},
        "bucket_counts_per_draw": [],
        "bucket_counts_overall": {name: 0 for name in bucket_names},
        "sums_per_draw": []
    }
    
    for draw in draws:
        odd_count = sum(1 for n in draw if n % 2 != 0)
        even_count = len(draw) - odd_count
        results["odd_even_per_draw"].append({"odd": odd_count, "even": even_count})
        results["odd_even_overall"]["odd"] += odd_count
        results["odd_even_overall"]["even"] += even_count
        
        low_count = sum(1 for n in draw if n <= low_max)
        high_count = len(draw) - low_count
        results["high_low_per_draw"].append({"high": high_count, "low": low_count})
        results["high_low_overall"]["high"] += high_count
        results["high_low_overall"]["low"] += low_count
        
        draw_sum = sum(draw)
        results["sums_per_draw"].append(draw_sum)
        
        draw_buckets = {name: 0 for name in bucket_names}
        for num in draw:
            for i, (start, end) in enumerate(buckets):
                if start <= num <= end:
                    draw_buckets[bucket_names[i]] += 1
                    results["bucket_counts_overall"][bucket_names[i]] += 1
                    break
        results["bucket_counts_per_draw"].append(draw_buckets)
        
    return results
