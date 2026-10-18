# PhantomStock AI — System Architecture

## Overview
PhantomStock AI bridges the gap between ERP recorded inventory ($>0$) and physical shelf availability ($0$) using a robust multi-signal scoring engine, FastAPI backend, React analytics dashboard, and automated n8n workflows.

---

## Architecture Diagram

```text
[ Retail POS & ERP Systems ]
             │
             ▼
   (Inbound CSV / Parquet)
             │
             ▼
┌─────────────────────────────────────────┐
│       1. DATA & GENERATION LAYER        │
│  - inventory_sales.csv                  │
│  - ground_truth_labels.csv              │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│     2. ANOMALY DETECTION ENGINE         │
│  - Consecutive Zero Sales Calculation   │
│  - Historical Demand Mismatch           │
│  - Inventory Volume & Price Weighting   │
│  - Zero Label Leakage Enforcement       │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│        3. EVALUATION & RANKING          │
│  - Top-20 Store Manager Constraint      │
│  - Precision@20 & Recall Calculation    │
└────────────────────┬────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────┐
│          4. FASTAPI BACKEND             │
│  - /api/status                          │
│  - /api/alerts (Top 20 filter)          │
│  - /api/sku-history & Chart Data        │
│  - /api/review-alert                    │
└────────────────────┬────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────────────┐ ┌─────────────────────────┐
│ 5. REACT DASHBOARD    │ │ 6. n8n AUTOMATION       │
│ - Tailwind UI         │ │ - Daily Schedule Trigger│
│ - Recharts Trajectory │ │ - HTTP Request to API   │
│ - Review Actions      │ │ - Automated Alerts      │
└───────────────────────┘ └─────────────────────────┘
```

---

## Core Components
1. **Detection Engine (`detector/engine.py`)**: Computes multi-signal anomaly scores without paid external LLM dependencies, ensuring low latency and high interpretability.
2. **Evaluator (`evaluate.py`)**: Strictly adheres to Precision@20 and Recall metrics on chronological test splits.
3. **FastAPI (`backend/main.py`)**: Production-ready asynchronous REST API.
4. **Dashboard (`frontend/`)**: Modern React SPA for store managers and inventory analysts.
5. **n8n Workflow (`n8n/phantom_stock_workflow.json`)**: Automated daily pipeline execution.
