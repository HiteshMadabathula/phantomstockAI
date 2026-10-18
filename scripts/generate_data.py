#!/usr/bin/env python3
"""
Generate realistic retail inventory & sales dataset and ground truth labels for PhantomStock AI.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_dataset(output_dir="data"):
    os.makedirs(output_dir, exist_ok=True)

    np.random.seed(42)

    stores = [f"STORE_{i:03d}" for i in range(1, 6)] # 5 stores
    categories = ["Grocery", "Electronics", "Apparel", "Home & Kitchen", "Beauty"]
    skus = [f"SKU_{i:04d}" for i in range(1, 51)] # 50 SKUs per store = 250 store-sku combinations

    sku_categories = {sku: np.random.choice(categories) for sku in skus}
    sku_base_prices = {sku: round(np.random.uniform(5.0, 150.0), 2) for sku in skus}

    start_date = datetime.strptime("2026-09-01", "%Y-%m-%d")
    dates = [start_date + timedelta(days=i) for i in range(30)] # 30 days of history

    records = []
    ground_truth = []

    for store in stores:
        for sku in skus:
            base_demand = np.random.uniform(2.0, 10.0)
            current_inv = np.random.randint(15, 80)
            consecutive_zeros = 0
            # Decide if this store-sku is prone to phantom stockouts (e.g. 15% of pairs)
            prone_to_phantom = np.random.random() < 0.20
            phantom_start_day = np.random.randint(5, 20) if prone_to_phantom else 999

            for day_idx, d in enumerate(dates):
                date_str = d.strftime("%Y-%m-%d")
                is_weekend = d.weekday() >= 5
                promoted = np.random.random() < 0.1

                is_phantom = 0
                if day_idx >= phantom_start_day and day_idx < phantom_start_day + 6 and current_inv > 5:
                    sales = 0
                    consecutive_zeros += 1
                    is_phantom = 1
                else:
                    if current_inv <= 0:
                        sales = 0
                        consecutive_zeros += 1
                    else:
                        lam = base_demand * (1.5 if promoted else 1.0) * (1.2 if is_weekend else 1.0)
                        sales = int(np.random.poisson(lam=max(0.5, lam)))
                        if sales > current_inv:
                            sales = current_inv
                        if sales == 0:
                            consecutive_zeros += 1
                        else:
                            consecutive_zeros = 0

                # Restock event occasionally
                received = np.random.choice([0, 25, 50], p=[0.8, 0.15, 0.05]) if current_inv < 15 else 0
                current_inv = max(0, current_inv - sales + received)
                if current_inv == 0 and not is_phantom:
                    current_inv = np.random.randint(20, 60) # automatic replenishment simulation

                records.append({
                    "store_id": store,
                    "sku_id": sku,
                    "date": date_str,
                    "category": sku_categories[sku],
                    "price": sku_base_prices[sku],
                    "recorded_inventory": int(current_inv),
                    "sales": int(sales),
                    "promoted": int(promoted),
                    "consecutive_zero_sales": int(consecutive_zeros)
                })

                ground_truth.append({
                    "store_id": store,
                    "sku_id": sku,
                    "date": date_str,
                    "is_phantom_stock": int(is_phantom)
                })

    df_sales = pd.DataFrame(records)
    df_truth = pd.DataFrame(ground_truth)

    sales_path = os.path.join(output_dir, "inventory_sales.csv")
    truth_path = os.path.join(output_dir, "ground_truth_labels.csv")

    df_sales.to_csv(sales_path, index=False)
    df_truth.to_csv(truth_path, index=False)

    print(f"Generated {len(df_sales)} sales records at {sales_path} (Phantoms: {df_truth['is_phantom_stock'].sum()})")
    print(f"Generated {len(df_truth)} ground truth labels at {truth_path}")

if __name__ == "__main__":
    generate_dataset()
