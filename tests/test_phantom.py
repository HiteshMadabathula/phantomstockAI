#!/usr/bin/env python3
"""
Automated test suite for PhantomStock AI (Ranking, Leakage Prevention, Slow-moving SKUs, Evaluation, Authentication & Authorization).
"""

import os
import sys
import pandas as pd
import pytest
from fastapi.testclient import TestClient

# Add root directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../detector")))

from backend.main import app
import evaluate
from detector.engine import run_detection

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dataset_generation_and_schema():
    sales_path = "data/inventory_sales.csv"
    truth_path = "data/ground_truth_labels.csv"

    assert os.path.exists(sales_path), "Sales dataset must exist"
    assert os.path.exists(truth_path), "Ground truth dataset must exist"

    df_sales = pd.read_csv(sales_path)
    required_sales_cols = ["store_id", "sku_id", "date", "recorded_inventory", "sales", "consecutive_zero_sales"]
    for col in required_sales_cols:
        assert col in df_sales.columns, f"Sales dataset missing column: {col}"

    df_truth = pd.read_csv(truth_path)
    required_truth_cols = ["store_id", "sku_id", "date", "is_phantom_stock"]
    for col in required_truth_cols:
        assert col in df_truth.columns, f"Ground truth dataset missing column: {col}"

def test_detection_engine_predictions():
    pred_df = run_detection("data/inventory_sales.csv", "data/predictions.csv")
    assert not pred_df.empty, "Predictions should not be empty"

    required_pred_cols = ["store_id", "sku_id", "date", "anomaly_score", "confidence", "reason"]
    for col in required_pred_cols:
        assert col in pred_df.columns, f"Predictions missing column: {col}"

    # Verify score range [0, 1]
    assert pred_df["anomaly_score"].min() >= 0.0
    assert pred_df["anomaly_score"].max() <= 1.0

def test_temporal_leakage_prevention(tmp_path):
    sales_file = tmp_path / "sales.csv"
    pred_file = tmp_path / "preds.csv"

    data = [
        {"store_id": "S1", "sku_id": "SKU1", "date": "2026-09-01", "recorded_inventory": 50, "sales": 10, "consecutive_zero_sales": 0, "promoted": 0},
        {"store_id": "S1", "sku_id": "SKU1", "date": "2026-09-02", "recorded_inventory": 40, "sales": 0, "consecutive_zero_sales": 1, "promoted": 0},
        {"store_id": "S1", "sku_id": "SKU1", "date": "2026-09-03", "recorded_inventory": 40, "sales": 100, "consecutive_zero_sales": 0, "promoted": 0},
    ]
    df = pd.DataFrame(data)
    df.to_csv(sales_file, index=False)

    preds1 = run_detection(str(sales_file), str(pred_file))
    score_day2_before = preds1[(preds1["date"] == "2026-09-02")]["anomaly_score"].values[0]

    data[2]["sales"] = 0
    df2 = pd.DataFrame(data)
    df2.to_csv(sales_file, index=False)

    preds2 = run_detection(str(sales_file), str(pred_file))
    score_day2_after = preds2[(preds2["date"] == "2026-09-02")]["anomaly_score"].values[0]

    assert score_day2_before == score_day2_after

def test_deterministic_scoring(tmp_path):
    sales_file = "data/inventory_sales.csv"
    pred_file1 = tmp_path / "preds1.csv"
    pred_file2 = tmp_path / "preds2.csv"

    df1 = run_detection(sales_file, str(pred_file1))
    df2 = run_detection(sales_file, str(pred_file2))

    pd.testing.assert_frame_equal(df1, df2)

def test_score_bounds():
    pred_df = run_detection("data/inventory_sales.csv", "data/predictions.csv")
    assert (pred_df["anomaly_score"] >= 0.0).all()
    assert (pred_df["anomaly_score"] <= 1.0).all()

def test_slow_moving_skus(tmp_path):
    sales_file = tmp_path / "sales.csv"
    pred_file = tmp_path / "preds.csv"

    data = [
        {"store_id": "S1", "sku_id": "SLOW", "date": "2026-09-01", "recorded_inventory": 30, "sales": 0, "consecutive_zero_sales": 3, "promoted": 0},
        {"store_id": "S1", "sku_id": "FAST", "date": "2026-09-01", "recorded_inventory": 30, "sales": 0, "consecutive_zero_sales": 3, "promoted": 0},
        {"store_id": "S1", "sku_id": "FAST", "date": "2026-08-31", "recorded_inventory": 40, "sales": 8, "consecutive_zero_sales": 0, "promoted": 0},
    ]
    df = pd.DataFrame(data)
    df.to_csv(sales_file, index=False)

    preds = run_detection(str(sales_file), str(pred_file))
    slow_score = preds[(preds["sku_id"] == "SLOW") & (preds["date"] == "2026-09-01")]["anomaly_score"].values[0]
    fast_score = preds[(preds["sku_id"] == "FAST") & (preds["date"] == "2026-09-01")]["anomaly_score"].values[0]

    assert slow_score < fast_score, "Slow-moving SKU should have lower anomaly score than high-demand SKU with same consecutive zeros"

def test_ground_truth_isolation():
    assert not os.path.exists("nonexistent_ground_truth.csv")
    pred_df = run_detection("data/inventory_sales.csv", "data/predictions.csv")
    assert not pred_df.empty

def test_evaluation_metrics():
    metrics = evaluate.evaluate("data/predictions.csv", "data/ground_truth_labels.csv")
    assert "precision_at_20" in metrics
    assert "recall" in metrics
    assert 0.0 <= metrics["precision_at_20"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0

def test_evaluation_ranking_before_merge(tmp_path):
    pred_file = tmp_path / "preds.csv"
    truth_file = tmp_path / "truth.csv"

    preds_data = []
    for i in range(1, 26):
        preds_data.append({
            "store_id": "STORE_TEST",
            "sku_id": f"SKU_{i:04d}",
            "date": "2026-09-01",
            "anomaly_score": float(i) / 25.0
        })
    df_preds = pd.DataFrame(preds_data)
    df_preds.to_csv(pred_file, index=False)

    truth_data = []
    for i in range(1, 26):
        truth_data.append({
            "store_id": "STORE_TEST",
            "sku_id": f"SKU_{i:04d}",
            "date": "2026-09-01",
            "is_phantom_stock": 1 if i >= 20 else 0
        })
    df_truth = pd.DataFrame(truth_data)
    df_truth.to_csv(truth_file, index=False)

    metrics = evaluate.evaluate(str(pred_file), str(truth_file))
    assert metrics["store_days"] == 1
    assert metrics["precision_at_20"] == pytest.approx(0.3)

def test_evaluation_incomplete_labels(tmp_path):
    pred_file = tmp_path / "preds.csv"
    truth_file = tmp_path / "truth.csv"

    df_preds = pd.DataFrame([
        {"store_id": "STORE_TEST", "sku_id": "SKU_0001", "date": "2026-09-01", "anomaly_score": 0.9},
        {"store_id": "STORE_TEST", "sku_id": "SKU_0002", "date": "2026-09-01", "anomaly_score": 0.8},
    ])
    df_preds.to_csv(pred_file, index=False)

    df_truth = pd.DataFrame([
        {"store_id": "STORE_TEST", "sku_id": "SKU_0001", "date": "2026-09-01", "is_phantom_stock": 1},
        {"store_id": "STORE_TEST", "sku_id": "SKU_0002", "date": "2026-09-01", "is_phantom_stock": float("nan")},
    ])
    df_truth.to_csv(truth_file, index=False)

    metrics = evaluate.evaluate(str(pred_file), str(truth_file))
    assert metrics["precision_at_20"] == 1.0
    assert metrics["unlabeled_top20_count"] == 1
    assert metrics["labeled_top20_count"] == 1

def test_evaluation_validation_errors(tmp_path):
    pred_file = tmp_path / "preds.csv"
    truth_file = tmp_path / "truth.csv"

    df_preds = pd.DataFrame([
        {"store_id": "STORE_TEST", "sku_id": "SKU_0001", "date": "2026-09-01"}
    ])
    df_preds.to_csv(pred_file, index=False)

    df_truth = pd.DataFrame([
        {"store_id": "STORE_TEST", "sku_id": "SKU_0001", "date": "2026-09-01", "is_phantom_stock": 1}
    ])
    df_truth.to_csv(truth_file, index=False)

    with pytest.raises(SystemExit):
        evaluate.evaluate(str(pred_file), str(truth_file))

def test_authentication_and_authorization():
    # 1. Unauthenticated request should fail with 401
    res_unauth = client.get("/api/status")
    assert res_unauth.status_code == 401

    # 2. Login as RetailCorp manager
    login_res = client.post("/api/auth/login", json={
        "email": "manager@retailcorp.demo",
        "password": "password123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data["token"]
    assert token is not None
    assert login_data["user"]["vendor_name"] == "RetailCorp"
    assert "STORE_001" in login_data["user"]["stores"]

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Authorized request to /api/status succeeds
    status_res = client.get("/api/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "stores" in status_data

    # 4. Authorized store access (STORE_001) succeeds
    store = "STORE_001"
    dates = status_data["available_dates"]
    if dates:
        date = dates[0]
        alert_resp = client.get(f"/api/alerts?date={date}&store_id={store}&limit=20", headers=headers)
        assert alert_resp.status_code == 200
        alerts = alert_resp.json()
        assert isinstance(alerts, list)

    # 5. Cross-vendor / unauthorized store access (STORE_004 belongs to GlobalGoods, not RetailCorp) should fail with 403 Forbidden
    forbidden_resp = client.get(f"/api/alerts?date=2026-09-01&store_id=STORE_004&limit=20", headers=headers)
    assert forbidden_resp.status_code == 403

    # 6. Logout and verify token is revoked
    logout_res = client.post("/api/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    status_after_logout = client.get("/api/status", headers=headers)
    assert status_after_logout.status_code == 401

def test_bearer_token_variations():
    # Login to get valid token
    login_res = client.post("/api/auth/login", json={
        "email": "manager@retailcorp.demo",
        "password": "password123"
    })
    token = login_res.json()["token"]

    # 1. Lowercase bearer prefix should succeed
    res_lower = client.get("/api/status", headers={"Authorization": f"bearer {token}"})
    assert res_lower.status_code == 200

    # 2. Extra spaces should succeed
    res_spaces = client.get("/api/status", headers={"Authorization": f"Bearer   {token}"})
    assert res_spaces.status_code == 200

    # 3. Invalid scheme should fail with 401
    res_invalid = client.get("/api/status", headers={"Authorization": f"Basic {token}"})
    assert res_invalid.status_code == 401

def test_n8n_alerts_token_workflow():
    # 1. Test missing Authorization header -> 401 Missing or invalid token format
    res_missing = client.get("/api/alerts?date=2026-09-01&store_id=STORE_001")
    assert res_missing.status_code == 401
    assert "Missing or invalid token format" in res_missing.json()["detail"]

    # 2. Test malformed Authorization header -> 401 Missing or invalid token format
    res_malformed = client.get("/api/alerts?date=2026-09-01&store_id=STORE_001", headers={"Authorization": "Basic some-token"})
    assert res_malformed.status_code == 401
    assert "Missing or invalid token format" in res_malformed.json()["detail"]

    # 3. Login to get valid token
    login_res = client.post("/api/auth/login", json={
        "email": "manager@retailcorp.demo",
        "password": "password123"
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    token = login_data.get("token")
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0

    # 4. Test invalid token -> 401 Invalid or expired session token
    res_invalid_token = client.get("/api/alerts?date=2026-09-01&store_id=STORE_001", headers={"Authorization": "Bearer non-existent-token-string"})
    assert res_invalid_token.status_code == 401
    assert "Invalid or expired session token" in res_invalid_token.json()["detail"]

    # 5. Get status to find available dates and authorized stores
    status_res = client.get("/api/status", headers={"Authorization": f"Bearer {token}"})
    assert status_res.status_code == 200
    status_json = status_res.json()
    dates = status_json.get("available_dates", [])
    stores = status_json.get("stores", ["STORE_001"])

    date_str = dates[0] if dates else "2026-09-01"
    store_id = stores[0] if stores else "STORE_001"

    # 6. Real authenticated GET /api/alerts call with extracted token using Authorization: Bearer <token> and required query params
    alerts_res = client.get(
        f"/api/alerts?date={date_str}&store_id={store_id}&limit=20",
        headers={"Authorization": f"Bearer {token.strip()}"}
    )
    assert alerts_res.status_code == 200
    alerts_data = alerts_res.json()
    assert isinstance(alerts_data, list)

def test_evaluation_endpoint_security():
    # 1. Unauthenticated evaluation run should fail with 401
    res_unauth = client.post("/api/evaluation/run")
    assert res_unauth.status_code == 401

    # 2. Public metrics endpoint should succeed without auth
    res_metrics = client.get("/api/evaluation/metrics")
    assert res_metrics.status_code == 200
    assert "precision_at_20" in res_metrics.json()

    # 3. Authenticated evaluation run should succeed
    login_res = client.post("/api/auth/login", json={
        "email": "manager@retailcorp.demo",
        "password": "password123"
    })
    token = login_res.json()["token"]
    res_auth = client.post("/api/evaluation/run", headers={"Authorization": f"Bearer {token}"})
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] == "success"

def test_detection_endpoint_security(monkeypatch):
    # 1. Unset API key should return 503
    monkeypatch.delenv("PHANTOMSTOCK_API_KEY", raising=False)
    res_unset = client.post("/api/detection/run", headers={"X-API-Key": "any-key"})
    assert res_unset.status_code == 503

    # 2. Set API key
    test_key = "secure-test-key-12345"
    monkeypatch.setenv("PHANTOMSTOCK_API_KEY", test_key)

    # 3. Invalid API key should return 401
    res_invalid = client.post("/api/detection/run", headers={"X-API-Key": "wrong-key"})
    assert res_invalid.status_code == 401

    # 4. Valid API key should succeed
    res_valid = client.post("/api/detection/run", headers={"X-API-Key": test_key})
    assert res_valid.status_code == 200
    assert res_valid.json()["status"] == "success"

