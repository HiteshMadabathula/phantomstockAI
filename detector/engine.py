#!/usr/bin/env python3
"""
PhantomStock AI Anomaly Detection Engine (R1. The Phantom Stock-Out Detector)
Computes multi-signal anomaly scores and generates plain-English explanations for store managers.
Eliminates temporal leakage, ensures deterministic scoring, and protects slow-moving SKUs.
"""

import os
import pandas as pd
import numpy as np

def run_detection(sales_path="data/inventory_sales.csv", output_path="data/predictions.csv"):
    if not os.path.exists(sales_path):
        raise FileNotFoundError(f"Sales data not found at {sales_path}")

    df = pd.read_csv(sales_path)

    # Ensure required columns
    required = ["store_id", "sku_id", "date", "recorded_inventory", "sales", "consecutive_zero_sales"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # 1. Sort chronologically for temporal leakage prevention
    df["date_dt"] = pd.to_datetime(df["date"])
    df = df.sort_values(["store_id", "sku_id", "date_dt"])

    # 2. Calculate chronological historical average sales (expanding window using only past dates < t)
    df["past_sales_valid"] = np.where(df["recorded_inventory"] > 0, df["sales"], np.nan)
    df["hist_avg_sales"] = df.groupby(["store_id", "sku_id"])["past_sales_valid"].apply(
        lambda g: g.expanding().mean().shift(1)
    ).reset_index(level=[0, 1], drop=True)

    # Fallback for SKUs with insufficient history: expanding mean of all past sales, then default to 1.0
    df["hist_avg_sales"] = df["hist_avg_sales"].fillna(
        df.groupby(["store_id", "sku_id"])["sales"].apply(lambda g: g.expanding().mean().shift(1)).reset_index(level=[0, 1], drop=True)
    ).fillna(1.0)

    # Weekend feature derivation
    df["is_weekend"] = df["date_dt"].dt.weekday >= 5

    scores = []
    confidences = []
    reasons = []

    for idx, row in df.iterrows():
        inv = row["recorded_inventory"]
        sales = row["sales"]
        zeros = row["consecutive_zero_sales"]
        avg_sales = row["hist_avg_sales"]
        promoted = bool(row.get("promoted", 0))
        is_weekend = bool(row.get("is_weekend", False))

        score = 0.0
        confidence = "Low"
        reason_parts = []

        if inv > 0 and sales == 0:
            # Base score from consecutive zero sales (max 0.5)
            zero_score = min(1.0, zeros / 7.0) * 0.5

            # Demand mismatch score weighted by expected demand (promotion and weekend boost expected baseline)
            demand_factor = avg_sales * (1.5 if promoted else 1.0) * (1.2 if is_weekend else 1.0)
            demand_score = min(1.0, demand_factor / 10.0) * 0.3

            # Inventory volume risk: high inventory sitting idle (max 0.2)
            inv_score = min(1.0, inv / 50.0) * 0.2

            score = zero_score + demand_score + inv_score
            score = max(0.0, min(1.0, score))  # Ensure strict bounds [0.0, 1.0]

            if zeros >= 5 and demand_factor >= 3.0:
                confidence = "High"
            elif zeros >= 3 and demand_factor >= 1.5:
                confidence = "Medium"
            else:
                confidence = "Low"

            # Plain English reason backed by actual input data
            reason_parts.append(f"{zeros} consecutive zero-sales days with {inv} units recorded.")
            if avg_sales > 0:
                reason_parts.append(f"Historical expected demand baseline is {avg_sales:.1f} units/day.")
            if promoted:
                reason_parts.append("Zero sales recorded during an active promotion event.")
            if inv > 30:
                reason_parts.append("High capital tied in idle stock.")
            reason = " ".join(reason_parts)
        else:
            # Deterministic score of 0.0 for normal records (no random noise)
            score = 0.0
            confidence = "Low"
            reason = "Normal inventory and sales flow."

        scores.append(round(float(score), 4))
        confidences.append(confidence)
        reasons.append(reason)

    df["anomaly_score"] = scores
    df["confidence"] = confidences
    df["reason"] = reasons

    # Select output columns for predictions
    pred_df = df[["store_id", "sku_id", "date", "anomaly_score", "confidence", "reason"]]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    pred_df.to_csv(output_path, index=False)
    print(f"Generated {len(pred_df)} predictions at {output_path}")
    return pred_df

if __name__ == "__main__":
    run_detection()
