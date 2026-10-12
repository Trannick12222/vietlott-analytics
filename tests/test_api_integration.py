import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_fetch_mega_data():
    response = client.post("/api/fetch", json={"lottery_type": "MEGA_645", "limit": 25})
    assert response.status_code == 200
    data = response.json()
    assert "records_added" in data
    assert data["lottery_type"] == "MEGA_645"

def test_fetch_power_data():
    response = client.post("/api/fetch", json={"lottery_type": "POWER_655", "limit": 25})
    assert response.status_code == 200
    data = response.json()
    assert "records_added" in data
    assert data["lottery_type"] == "POWER_655"

def test_get_draws():
    response = client.get("/api/draws/MEGA_645?limit=20")
    assert response.status_code == 200
    draws = response.json()
    assert len(draws) > 0
    assert len(draws[0]["numbers"]) == 6

def test_get_statistics():
    response = client.get("/api/statistics/MEGA_645")
    assert response.status_code == 200
    stats = response.json()
    assert "frequency" in stats
    assert "recency" in stats
    assert "bayesian" in stats
    assert "probability" in stats

def test_get_predictions():
    response = client.get("/api/predictions/MEGA_645?threshold=50")
    assert response.status_code == 200
    preds = response.json()
    assert "rankings" in preds
    assert "combinations" in preds
    assert "mathematical_probability" in preds
    assert "disclaimer" in preds
    assert all(r["model_score"] >= 50 for r in preds["rankings"])
    assert any("MODEL SCORE" in preds["disclaimer"].upper() or "MODEL SCORE" in preds.get("sample_size_warning", "").upper() or "Model Score" in preds["disclaimer"] for _ in [1])

def test_predictions_threshold_filter_empty():
    response = client.get("/api/predictions/MEGA_645?threshold=99.9")
    assert response.status_code == 200
    preds = response.json()
    assert preds["no_numbers_passed"] is True
    assert len(preds["rankings"]) == 0


def test_get_backtest():
    response = client.get("/api/backtest/MEGA_645")
    assert response.status_code == 200
    bt = response.json()
    assert "status" in bt
    assert "better_than_random" in bt

def test_get_dashboard():
    response = client.get("/api/dashboard/MEGA_645")
    assert response.status_code == 200
    dash = response.json()
    assert "latest_draws" in dash
    assert "statistics" in dash
    assert "predictions" in dash

def test_frontend_routes():
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "VIETLOTT ANALYTICS" in res_home.text or "Vietlott" in res_home.text

    res_dash = client.get("/dashboard/MEGA_645")
    assert res_dash.status_code == 200

def test_get_bao_combinations():
    response = client.get("/api/combinations/bao/MEGA_645?bao_type=7")
    assert response.status_code == 200
    data = response.json()
    assert data["bao_type"] == 7
    assert data["ticket_count"] == 7
    assert data["cost"] == 70_000
    assert len(data["combinations"]) == 5
    for c in data["combinations"]:
        assert len(c["numbers"]) == 7

def test_get_wheeling_combinations():
    response = client.get("/api/combinations/wheeling/MEGA_645?wheel_size=12")
    assert response.status_code == 200
    data = response.json()
    assert data["wheel_size"] == 12
    assert data["ticket_count"] == 6
    assert data["cost"] == 60_000
    assert data["full_bao_cost"] == 9_240_000
    assert data["savings_pct"] > 99.0
    assert len(data["tickets"]) == 6
    for t in data["tickets"]:
        assert len(t) == 6
        assert len(set(t)) == 6

def test_optimize_custom_combinations():
    payload = {
        "lottery_type": "MEGA_645",
        "numbers": [3, 6, 11, 19, 20, 23, 24, 26, 30, 43],
        "ticket_count": 8
    }
    response = client.post("/api/combinations/custom", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["pool_size"] == 10
    assert data["ticket_count"] == 8
    assert len(data["tickets"]) == 8
    assert data["cost"] == 80_000
    assert data["savings_pct"] > 95.0
    for t in data["tickets"]:
        assert len(t["numbers"]) == 6
        assert t["fitness"] > 0
        assert "odd_even" in t
        assert "sum" in t
    assert "suitability" in data
    assert data["suitability"]["recommended"] in ("MEGA_645", "POWER_655")

def test_evaluate_suitability_power():
    # Test pool with numbers > 45 must recommend Power 6/55
    res = client.post("/api/combinations/evaluate-suitability", json={"numbers": [3, 6, 11, 19, 20, 23, 48, 52]})
    assert res.status_code == 200
    data = res.json()
    assert data["recommended"] == "POWER_655"
    assert data["is_mandatory"] is True
    assert data["power_pct"] == 100.0

def test_evaluate_suitability_mega():
    # Test pool with low numbers should recommend Mega 6/45
    res = client.post("/api/combinations/evaluate-suitability", json={"numbers": [3, 6, 11, 15, 19, 20, 24, 26, 30]})
    assert res.status_code == 200
    data = res.json()
    assert data["recommended"] == "MEGA_645"
    assert data["mega_pct"] > 50.0


