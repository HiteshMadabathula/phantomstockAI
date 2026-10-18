# PhantomStock AI — Retail Inventory Anomaly Detection System (Problem R1)

PhantomStock AI is an enterprise-grade, hackathon-winning solution for **"R1. The Phantom Stock-Out Detector."** It identifies SKU-store-day combinations where recorded inventory is positive ($>0$) but actual shelf availability is zero, ranking suspicious items so store managers inspect no more than **20 SKUs per day**.

---

## Key Features

1. **Multi-Signal Anomaly Detection Engine**: Analyzes consecutive zero-sales days, historical demand mismatch, recorded inventory volume, promotions, and weekday patterns without requiring paid external LLM APIs.
2. **Top-20 Store Manager Constraint**: Automatically ranks and filters alerts so store staff never exceed 20 physical audits per day.
3. **Zero Data Leakage Architecture**: Strict chronological train/test partitioning and withheld ground truth labels during inference.
4. **FastAPI High-Performance Backend**: REST endpoints for status, alerts, SKU investigation history, chart trajectories, and evaluation metrics.
5. **Polished React Dashboard**: Modern Tailwind CSS interface with store/date filters, ranked alert table, detail chart modal, alert review actions (Confirmed, Not Phantom, Investigating), and annual recovery estimate ($45,192/yr).
6. **n8n Automated Workflow**: Ready-to-import n8n automation JSON for daily schedule triggers, dataset checks, API requests, and top-20 rule validation.
7. **Comprehensive Pytest Suite**: Automated tests covering ranking, leakage prevention, slow-moving SKUs, missing data, and evaluation.

---

## Project Structure

```text
AP/
├── backend/
│   └── main.py                # FastAPI REST server
├── detector/
│   └── engine.py              # Multi-signal anomaly detection engine
├── frontend/                  # React dashboard (Vite + Tailwind + Recharts)
│   ├── src/App.jsx
│   ├── package.json
│   └── vite.config.ts
├── n8n/
│   └── phantom_stock_workflow.json # Importable n8n workflow
├── scripts/
│   └── generate_data.py       # Synthetic dataset & ground truth generator
├── tests/
│   └── test_phantom.py        # Comprehensive pytest test suite
├── data/
│   ├── inventory_sales.csv    # Generated sales & inventory dataset
│   ├── ground_truth_labels.csv# Ground truth phantom stock labels
│   └── predictions.csv        # Generated anomaly score predictions
├── evaluate.py                # Official evaluation script (Precision@20 & Recall)
├── architecture.md            # System architecture documentation
├── pitch.md                   # Hackathon elevator pitch
└── README.md                  # User guide & documentation
```

---

## Installation & Quickstart

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ (for frontend dashboard)

### 2. Install Python Dependencies
```bash
pip install pandas numpy scikit-learn fastapi uvicorn pydantic pytest httpx
```

### 3. Generate Dataset & Run Detection
```bash
python scripts/generate_data.py
python detector/engine.py
python evaluate.py
```

### 4. Run Automated Tests
```bash
pytest
```

### 5. Start FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
*(API docs available at `http://localhost:8000/docs`)*

### 6. Start React Dashboard
```cd frontend
npm install
npm run dev
```
*(Dashboard available at `http://localhost:3000`)*

---

## Evaluation & Metrics

`evaluate.py` evaluates model predictions against authorized ground truth labels:
- **Precision@20**: Measures the fraction of true phantom stock-outs in the top 20 alerts per store-day.
- **Recall**: Measures the fraction of all true phantom stock-outs successfully captured.
- **Estimated Annual Recovery**: Calculated based on lost sales prevented, retail gross margins, and store traffic factors.

---

## n8n Workflow Integration
1. Open n8n (`http://localhost:5678` or cloud instance).
2. Import `n8n/phantom_stock_workflow.json`.
3. Configure HTTP Request node to point to your deployed FastAPI backend (`/api/alerts`).
4. Activate the Daily Schedule Trigger.
