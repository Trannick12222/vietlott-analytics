import math
from typing import List, Dict, Any, Tuple

def analyze_regime_and_extremes(draws: List[List[int]], lottery_type: str = "mega") -> Dict[str, Any]:
    """
    Phân tích Thống kê Thứ tự Cực trị (Order Statistics),
    Xác suất Trạng thái Siêu bội (Hypergeometric Regime Detection),
    Ma trận Chuyển dịch Markov và Lực hút Hồi quy Trung bình (Mean Reversion Oscillator).
    """
    if not draws:
        return {}

    is_mega = (lottery_type.lower() == "mega")
    max_num = 45 if is_mega else 55
    k = 6

    # 1. THỐNG KÊ THỨ TỰ CỰC TRỊ LÝ THUYẾT (ORDER STATISTICS)
    # E[X_(i)] = i * (N + 1) / (k + 1)
    theo_min = round((max_num + 1) / (k + 1), 2)
    theo_max = round((k * (max_num + 1)) / (k + 1), 2)
    theo_span = round(theo_max - theo_min, 2)

    # Khoảng tin cậy lý thuyết 90%
    if is_mega:
        min_ci = [1, 14]
        max_max_ci = [32, 45]
        low_threshold = 33
        std_threshold = 42
        mu_sum = 138.0
        sigma_sum = 33.7
    else:
        min_ci = [1, 16]
        max_max_ci = [39, 55]
        low_threshold = 40
        std_threshold = 50
        mu_sum = 168.0
        sigma_sum = 44.5

    # 2. XÁC SUẤT TOÁN HỌC LÝ THUYẾT (HYPERGEOMETRIC COMBINATORICS)
    c_total = math.comb(max_num, k)
    c_low = math.comb(low_threshold, k)
    c_std_cum = math.comb(std_threshold, k)
    
    theory_pct_low = round((c_low / c_total) * 100.0, 2)
    theory_pct_std = round(((c_std_cum - c_low) / c_total) * 100.0, 2)
    theory_pct_high = round(((c_total - c_std_cum) / c_total) * 100.0, 2)

    # 3. DỮ LIỆU THỰC CHỨNG TỪ LỊCH SỬ KỲ QUAY
    min_balls = [min(d) for d in draws]
    max_balls = [max(d) for d in draws]
    spans = [max(d) - min(d) for d in draws]
    sums = [sum(d) for d in draws]

    emp_avg_min = round(sum(min_balls) / len(min_balls), 2)
    emp_avg_max = round(sum(max_balls) / len(max_balls), 2)
    emp_avg_span = round(sum(spans) / len(spans), 2)

    # Phân loại trạng thái lịch sử
    historical_regimes = []
    for d in draws:
        m = max(d)
        if m <= low_threshold:
            historical_regimes.append("LOW")
        elif m <= std_threshold:
            historical_regimes.append("STD")
        else:
            historical_regimes.append("HIGH")

    counts = {
        "LOW": historical_regimes.count("LOW"),
        "STD": historical_regimes.count("STD"),
        "HIGH": historical_regimes.count("HIGH")
    }
    total_d = len(draws)
    emp_pct = {
        "LOW": round((counts["LOW"] / total_d) * 100.0, 1),
        "STD": round((counts["STD"] / total_d) * 100.0, 1),
        "HIGH": round((counts["HIGH"] / total_d) * 100.0, 1)
    }

    # 4. MA TRẬN CHUYỂN DỊCH MARKOV (1-STEP MARKOV CHAIN)
    trans_counts = {
        "LOW": {"LOW": 0, "STD": 0, "HIGH": 0},
        "STD": {"LOW": 0, "STD": 0, "HIGH": 0},
        "HIGH": {"LOW": 0, "STD": 0, "HIGH": 0}
    }
    for i in range(len(historical_regimes) - 1):
        curr_r = historical_regimes[i]
        next_r = historical_regimes[i + 1]
        trans_counts[curr_r][next_r] += 1

    trans_prob = {}
    for r_from, to_dict in trans_counts.items():
        row_sum = sum(to_dict.values())
        trans_prob[r_from] = {}
        for r_to, count in to_dict.items():
            if row_sum > 0:
                trans_prob[r_from][r_to] = round((count / row_sum) * 100.0, 1)
            else:
                trans_prob[r_from][r_to] = theory_pct_low if r_to == "LOW" else (theory_pct_std if r_to == "STD" else theory_pct_high)

    current_regime = historical_regimes[-1] if historical_regimes else "STD"

    # Kết hợp Bayesian giữa Xác suất tiên nghiệm (Lý thuyết) và Chuyển dịch Markov
    markov_next = trans_prob.get(current_regime, {
        "LOW": theory_pct_low,
        "STD": theory_pct_std,
        "HIGH": theory_pct_high
    })

    # Posterior Bayes: kết hợp 40% Lý thuyết tổ hợp + 60% Ma trận Markov lịch sử
    p_low_post = 0.4 * theory_pct_low + 0.6 * markov_next.get("LOW", theory_pct_low)
    p_std_post = 0.4 * theory_pct_std + 0.6 * markov_next.get("STD", theory_pct_std)
    p_high_post = 0.4 * theory_pct_high + 0.6 * markov_next.get("HIGH", theory_pct_high)
    sum_post = p_low_post + p_std_post + p_high_post
    if sum_post > 0:
        p_low_post = round((p_low_post / sum_post) * 100.0, 1)
        p_std_post = round((p_std_post / sum_post) * 100.0, 1)
        p_high_post = round((p_high_post / sum_post) * 100.0, 1)

    # Xác định trạng thái dự báo cao nhất cho kỳ tiếp theo
    pred_dict = {"LOW": p_low_post, "STD": p_std_post, "HIGH": p_high_post}
    predicted_regime = max(pred_dict, key=pred_dict.get)

    # 5. LỰC HÚT HỒI QUY VỀ TRUNG BÌNH (MEAN REVERSION OSCILLATOR)
    recent_3_draws = draws[-3:] if len(draws) >= 3 else draws
    recent_sums = [sum(d) for d in recent_3_draws]
    recent_maxs = [max(d) for d in recent_3_draws]
    recent_avg_sum = round(sum(recent_sums) / len(recent_sums), 1)
    recent_avg_max = round(sum(recent_maxs) / len(recent_maxs), 1)

    z_sum = round((recent_avg_sum - mu_sum) / sigma_sum, 2)
    sigma_max = 6.8
    z_max = round((recent_avg_max - theo_max) / sigma_max, 2)

    if z_sum >= 0.8:
        reversion_status = "OVERBOUGHT_HIGH"
        reversion_desc = "Dải tổng và bóng cực đại đang quá cao liên tiếp -> Lực hút hồi quy mạnh về dải Thấp/Trung để cân bằng trọng tâm."
        pull_direction = "TOWARD_LOW_MID"
    elif z_sum <= -0.8:
        reversion_status = "OVERSOLD_LOW"
        reversion_desc = "Dải tổng và bóng cực đại đang bị nén thấp -> Lực hút hồi quy chuẩn bị bung về dải Cao để trả nhịp chuẩn."
        pull_direction = "TOWARD_HIGH"
    else:
        reversion_status = "BALANCED"
        reversion_desc = "Phân phối dao động ổn định quanh trục tâm chuẩn Gauss."
        pull_direction = "STABLE"

    # Trọng số điểm hồi quy cho từng con số [1..max_num]
    reversion_number_scores = {}
    for num in range(1, max_num + 1):
        if pull_direction == "TOWARD_LOW_MID":
            # Ưu tiên các số nhỏ và trung bình
            if num <= low_threshold:
                reversion_number_scores[num] = 85.0 - (num / low_threshold) * 15.0
            else:
                reversion_number_scores[num] = max(20.0, 50.0 - ((num - low_threshold) / (max_num - low_threshold)) * 30.0)
        elif pull_direction == "TOWARD_HIGH":
            # Ưu tiên các số cao
            if num > low_threshold:
                reversion_number_scores[num] = 70.0 + ((num - low_threshold) / (max_num - low_threshold)) * 25.0
            else:
                reversion_number_scores[num] = max(20.0, 55.0 - ((low_threshold - num) / low_threshold) * 25.0)
        else:
            # Ổn định hình chuông
            dist_from_mid = abs(num - (max_num / 2.0))
            reversion_number_scores[num] = 75.0 - (dist_from_mid / (max_num / 2.0)) * 25.0

    # Vùng dự báo chi tiết cho kỳ tiếp theo
    if predicted_regime == "LOW":
        expected_min_range = [1, 9]
        expected_max_range = [23, low_threshold]
        expected_sum_range = [int(mu_sum - 1.5 * sigma_sum), int(mu_sum - 0.5 * sigma_sum)]
    elif predicted_regime == "STD":
        expected_min_range = [3, 13]
        expected_max_range = [low_threshold + 1, std_threshold]
        expected_sum_range = [int(mu_sum - 0.7 * sigma_sum), int(mu_sum + 0.7 * sigma_sum)]
    else:
        expected_min_range = [5, 16]
        expected_max_range = [std_threshold + 1, max_num]
        expected_sum_range = [int(mu_sum + 0.3 * sigma_sum), int(mu_sum + 1.5 * sigma_sum)]

    latest_draw = draws[-1]
    latest_min = min(latest_draw)
    latest_max = max(latest_draw)
    latest_span = latest_max - latest_min

    return {
        "lottery_type": lottery_type,
        "order_statistics": {
            "theoretical_min": theo_min,
            "theoretical_max": theo_max,
            "theoretical_span": theo_span,
            "empirical_avg_min": emp_avg_min,
            "empirical_avg_max": emp_avg_max,
            "empirical_avg_span": emp_avg_span,
            "latest_min": latest_min,
            "latest_max": latest_max,
            "latest_span": latest_span,
            "min_confidence_interval": min_ci,
            "max_confidence_interval": max_max_ci
        },
        "regime_analysis": {
            "regimes_definition": {
                "LOW": {
                    "code": "LOW",
                    "name": "Nén dải thấp (Low Compression)",
                    "range": f"01 - {low_threshold}",
                    "theory_pct": theory_pct_low
                },
                "STD": {
                    "code": "STD",
                    "name": "Cân bằng chuẩn (Standard Bell)",
                    "range": f"{low_threshold + 1} - {std_threshold}",
                    "theory_pct": theory_pct_std
                },
                "HIGH": {
                    "code": "HIGH",
                    "name": "Bung dải cao (High Extreme)",
                    "range": f"{std_threshold + 1} - {max_num}",
                    "theory_pct": theory_pct_high
                }
            },
            "empirical_counts": counts,
            "empirical_pct": emp_pct,
            "current_regime": current_regime,
            "transition_matrix": trans_prob,
            "next_draw_forecast": {
                "predicted_regime": predicted_regime,
                "probabilities": {
                    "LOW": p_low_post,
                    "STD": p_std_post,
                    "HIGH": p_high_post
                },
                "confidence": "High" if max(p_low_post, p_std_post, p_high_post) >= 48 else "Medium",
                "expected_min_range": expected_min_range,
                "expected_max_range": expected_max_range,
                "expected_sum_range": expected_sum_range
            }
        },
        "mean_reversion": {
            "mu_sum": mu_sum,
            "sigma_sum": sigma_sum,
            "recent_avg_sum": recent_avg_sum,
            "z_score_sum": z_sum,
            "recent_avg_max": recent_avg_max,
            "z_score_max": z_max,
            "reversion_status": reversion_status,
            "reversion_desc": reversion_desc,
            "pull_direction": pull_direction,
            "per_number_scores": reversion_number_scores
        }
    }
