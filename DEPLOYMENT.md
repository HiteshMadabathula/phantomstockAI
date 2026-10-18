# PhantomStock AI — Deployment & Security Guide

## Overview
PhantomStock AI is an advanced retail inventory anomaly detection system (R1 Phantom Stock-Out Detector) featuring a FastAPI backend, a React / Vite frontend SPA, SQLite-backed user authentication and store-level authorization, and a multi-signal anomaly detection engine.

---

## 1. Environment Variables

Create a `.env` file in the project root directory or configure environment variables in your deployment platform:

```env
# Required for n8n / webhook detection automation triggers
PHANTOMSTOCK_API_KEY=your-secure-api-key-here
```

*Note: If `PHANTOMSTOCK_API_KEY` is unset, `POST /api/detection/run` will safely fail with HTTP 503 to prevent unauthenticated execution.*

---

## 2. Setup & Installation

### Backend (Python FastAPI)
1. Ensure Python 3.10+ is installed.
2. Install dependencies:
   ```bash
   pip install fastapi uvicorn pandas numpy pytest httpx
   ```
3. Run the backend development server:
   ```bash
   python backend/main.py
   ```
   *(Or using uvicorn directly: `uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload`)*

### Frontend (React / Vite)
1. Ensure Node.js 18+ is installed.
2. Install dependencies and build:
   ```bash
   cd frontend
   npm install
   npm run build
   ```
3. The FastAPI backend automatically serves the production build from `frontend/dist/`.

---

## 3. Seeded Demo Accounts

PhantomStock AI automatically seeds the SQLite database (`data/phantom_users.db`) on startup with two role-based demo vendor accounts:

1. **RetailCorp (Store Operations Director)**
   - **Email:** `manager@retailcorp.demo`
   - **Password:** `password123`
   - **Authorized Stores:** `STORE_001`, `STORE_002`, `STORE_003`

2. **GlobalGoods (Supply Chain Manager)**
   - **Email:** `ops@globalgoods.demo`
   - **Password:** `password123`
   - **Authorized Stores:** `STORE_004`, `STORE_005`

---

## 4. n8n Automation & Webhook Configuration

To trigger automated inventory anomaly detection runs from n8n or external orchestration tools:

- **Endpoint:** `POST /http://<server-ip>:8000/api/detection/run`
- **Required Header:** `X-API-Key: <your-secure-api-key-here>`
- **Behavior:** Validates the API key using constant-time comparison (`secrets.compare_digest`), runs the detection engine against `data/inventory_sales.csv`, updates `data/predictions.csv`, and returns prediction counts.

---

## 5. Database Persistence & Storage

- **SQLite Database:** Stored at `data/phantom_users.db`. Contains hashed passwords (PBKDF2-SHA256 with 100,000 iterations and random salts) and active session tokens.
- **Persistence Requirement:** Ensure the `data/` directory is mounted onto persistent disk storage in containerized deployments (Docker/Kubernetes) to prevent loss of user sessions and review statuses on container restart.
- **Git Exclusions:** `.gitignore` excludes `data/*.db`, `data/alert_reviews.json`, `data/predictions.csv`, `.env`, and caches. Challenge datasets (`inventory_sales.csv` and `ground_truth_labels.csv`) remain tracked.

---

## 6. Security Limitations & Production Considerations

- **Single-Node Deployment:** The built-in SQLite session store is designed for single-node deployments and hackathon environments. For distributed multi-instance production clusters, replace session storage with Redis or JWT-based stateless tokens.
- **Transport Security:** Always deploy behind HTTPS (TLS termination via Nginx, Caddy, or cloud load balancer) to secure Bearer tokens in transit.
- **CORS Configuration:** Configured for demo convenience (`allow_origins=["*"]`). Restrict allowed origins to trusted domains in production.
