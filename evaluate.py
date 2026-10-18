#!/usr/bin/env python3
"""
PhantomStock AI Evaluation Script (R1. The Phantom Stock-Out Detector)
Evaluates ranked predictions against ground truth labels using Precision@20 and Recall.
"""

import sys
import os
import pandas as pd
import numpy as np

def evaluate(pred_path="data/predictions.csv", truth_path="data/ground_truth_labels.csv"):
    if not os.path.exists(pred_path):
        print(f"Error: Predictions file not found at {pred_path}")
        sys.exit(1)
    if not os.path.exists(truth_path):
        print(f"Error: Ground truth file not found at {truth_path}")
        sys.exit(1)

    try:
        preds = pd.read_csv(pred_path)
    except Exception as e:
        print(f"Error reading predictions CSV: {e}")
        sys.exit(1)

    try:
        truth = pd.read_csv(truth_path)
    except Exception as e:
        print(f"Error reading ground truth CSV: {e}")
        sys.exit(1)

    # 4. Validation: Required columns check
    pred_required = ["store_id", "sku_id", "date", "anomaly_score"]
    for col in pred_required:
        if col not in preds.columns:
            print(f"Error: Missing required column '{col}' in predictions.")
            sys.exit(1)

    truth_required = ["store_id", "sku_id", "date", "is_phantom_stock"]
    for col in truth_required:
        if col not in truth.columns:
            print(f"Error: Missing required column '{col}' in ground truth.")
            sys.exit(1)

    # 4. Validation: Duplicate keys check
    if preds.duplicated(subset=["store_id", "sku_id", "date"]).any():
        print("Error: Duplicate prediction keys (store_id, sku_id, date) found in predictions.")
        sys.exit(1)

    if truth.duplicated(subset=["store_id", "sku_id", "date"]).any():
        print("Error: Duplicate ground truth keys (store_id, sku_id, date) found in ground truth.")
        sys.exit(1)

    # 4. Validation: Missing / non-numeric anomaly scores check
    if preds["anomaly_score"].isna().any():
        print("Error: Predictions contain missing (NaN) anomaly_score values.")
        sys.exit(1)

    anomaly_numeric = pd.to_numeric(preds["anomaly_score"], errors="coerce")
    if anomaly_numeric.isna().any():
        print("Error: Predictions contain non-numeric anomaly_score values.")
        sys.exit(1)
    preds["anomaly_score"] = anomaly_numeric

    # 4. Validation: Binary ground-truth labels check (allowing NaN for incomplete labels)
    non_null_labels = truth["is_phantom_stock"].dropna()
    if not non_null_labels.empty:
        invalid_labels = non_null_labels[~non_null_labels.isin([0, 1, 0.0, 1.0])]
        if len(invalid_labels) > 0:
            print(f"Error: Ground truth contains invalid non-binary labels in 'is_phantom_stock': {invalid_labels.unique()}. Expected binary 0 or 1.")
            sys.exit(1)

    if len(preds) == 0:
        print("Warning: Predictions dataset is empty.")
        return {
            "precision_at_20": 0.0,
            "recall": 0.0,
            "store_days": 0,
            "total_phantoms": 0,
            "identified_phantoms": 0,
            "labeled_top20_count": 0,
            "unlabeled_top20_count": 0
        }

    # 1. Rank all prediction rows by anomaly_score descending, separately for each store_id and date, BEFORE joining ground-truth labels.
    preds_sorted = preds.sort_values(["store_id", "date", "anomaly_score"], ascending=[True, True, False])
    preds_sorted["rank"] = preds_sorted.groupby(["store_id", "date"]).cumcount() + 1

    # 2. Select the top 20 predictions per store-day. If fewer than 20 predictions exist, select all available candidates.
    top_20 = preds_sorted[preds_sorted["rank"] <= 20].copy()

    # 3. Join selected predictions to ground truth using store_id, sku_id, and date.
    merged = pd.merge(top_20, truth, on=["store_id", "sku_id", "date"], how="left")

    if len(merged) == 0:
        print("Warning: Merged dataset is empty. Check store_id, sku_id, and date formats.")
        return {
            "precision_at_20": 0.0,
            "recall": 0.0,
            "store_days": 0,
            "total_phantoms": 0,
            "identified_phantoms": 0,
            "labeled_top20_count": 0,
            "unlabeled_top20_count": 0
        }

    # 5. Handle incomplete ground-truth labels & Precision@20 calculation
    unlabeled_mask = merged["is_phantom_stock"].isna()
    unlabeled_count = int(unlabeled_mask.sum())
    labeled_count = int((~unlabeled_mask).sum())

    if unlabeled_count > 0:
        print(f"[Notice] Ground-truth labels are incomplete: {unlabeled_count} out of {len(merged)} top-20 predictions are unlabeled.")
        print("         Unlabeled candidates are excluded from Precision@20 denominator (computed over labeled top-20 predictions only).")
    else:
        print("[Notice] Ground-truth labels are complete for all top-20 predictions.")

    labeled_top20 = merged[~merged["is_phantom_stock"].isna()].copy()

    if len(labeled_top20) > 0:
        p20_per_store_day = labeled_top20.groupby(["store_id", "date"])["is_phantom_stock"].mean()
        mean_precision_at_20 = float(p20_per_store_day.mean())
        store_days_evaluated = int(len(p20_per_store_day))
    else:
        mean_precision_at_20 = 0.0
        store_days_evaluated = 0

    # 6. Recall calculation using available ground-truth labels
    valid_truth = truth.dropna(subset=["is_phantom_stock"])
    total_actual_phantoms = int(valid_truth["is_phantom_stock"].sum())
    identified_phantoms = int(merged[(merged["is_phantom_stock"] == 1)].shape[0])
    recall = float(identified_phantoms / total_actual_phantoms) if total_actual_phantoms > 0 else 0.0

    # 9. Print readable evaluation results
    print("=" * 65)
    print("PHANTOMSTOCK AI — EVALUATION RESULTS")
    print("=" * 65)
    print(f"Store-Days Evaluated (Precision): {store_days_evaluated}")
    print(f"Mean Precision@20:                {mean_precision_at_20:.4f} ({mean_precision_at_20 * 100:.2f}%)")
    print(f"Overall Recall:                   {recall:.4f} ({recall * 100:.2f}%)")
    print(f"Total True Phantoms (Ground Truth): {total_actual_phantoms}")
    print(f"Identified in Top 20:             {identified_phantoms}")
    print(f"Top-20 Labeled / Unlabeled:       {labeled_count} / {unlabeled_count}")
    print(f"Ground Truth Coverage:            {len(valid_truth)} labeled rows out of {len(truth)} total ground truth rows.")
    print("=" * 65)

    return {
        "precision_at_20": mean_precision_at_20,
        "recall": recall,
        "store_days": store_days_evaluated,
        "total_phantoms": total_actual_phantoms,
        "identified_phantoms": identified_phantoms,
        "labeled_top20_count": labeled_count,
        "unlabeled_top20_count": unlabeled_count
    }

if __name__ == "__main__":
    pred_file = sys.argv[1] if len(sys.argv) > 1 else "data/predictions.csv"
    truth_file = sys.argv[2] if len(sys.argv) > 2 else "data/ground_truth_labels.csv"
    evaluate(pred_file, truth_file)
