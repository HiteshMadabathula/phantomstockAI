# PhantomStock AI — Hackathon Elevator Pitch

## The Problem
Retailers lose billions globally to **Phantom Stock-Outs** — items where ERP inventory shows positive stock ($>0$), but physical shelves are empty due to theft, unrecorded shrinkage, misplaced backroom inventory, or scanner errors. Because ERP systems think stock is present, automated reordering never triggers, customers experience out-of-stocks, and top-line revenue leaks away.

## Our Solution: PhantomStock AI
PhantomStock AI is an end-to-end intelligent detection and resolution system designed for retail store managers:
1. **Multi-Signal Anomaly Detection**: Identifies hidden discrepancies by combining consecutive zero-sales days, historical demand baselines, and inventory volume without relying on expensive, slow LLM API calls for every SKU.
2. **The Store Manager Top-20 Rule**: Automatically ranks suspicious items so store staff inspect no more than **20 SKUs per day**, eliminating audit fatigue.
3. **Actionable Plain-English Explanations**: Every alert comes with a clear rationale (e.g., *“5 consecutive zero-sales days with 42 units recorded; historical demand is 4.1 units/day”*).
4. **Instant ROI & Recovery Dashboard**: Visualizes time-series trajectories, tracks review actions (*Confirmed Phantom*, *Not Phantom*, *Investigating*), and projects annual lost-sales recovery ($45,192+/year per store).
5. **Seamless Automation**: Fully integrated with n8n for scheduled daily detection runs and automated notifications.

## Why We Win
- **Zero Leakage & Rigorous Evaluation**: Chronological train/test separation with strict label withholding and automated Precision@20 / Recall validation via `evaluate.py`.
- **Production-Ready Stack**: FastAPI backend, React Tailwind dashboard, pytest suite, and importable n8n workflow.
- **Immediate Business Impact**: Turns invisible inventory discrepancies into verified shelf availability in minutes.
