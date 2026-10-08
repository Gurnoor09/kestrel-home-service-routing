# Kestrel Home Appliances — Service Request Intelligent Router

A lightweight, high-performance, and cost-effective machine learning routing engine designed to replace the legacy third-party vendor routing bot for Kestrel Home Appliances.

---

## 1. Business Problem & Context

Kestrel Home Appliances operates a high-volume direct-to-consumer service desk receiving inbound customer service requests across multiple channels (IVR transcript, Chat, WhatsApp, Email).

* **Current Challenge:** Inbound routing is currently handled by a third-party vendor bot under an annual licence of **Rs 3,20,000 / year**. The client seeks to retire this bot with an in-house ML model that matches or exceeds a **90.0%** routing accuracy threshold.
* **Service Queues:** Requests must be routed into one of **7 canonical queues**:
  1. `Repairs` (breakdowns, noise, leaks, error codes, electrical trips)
  2. `Billing` (invoice, GST, double charges, refunds, payment issues)
  3. `Filters & Consumables` (spare parts, candles, membranes, AMC kits)
  4. `Installs & Demo` (new-device installation, demo, wall-mounting visits)
  5. `Product Advice` (usage, recipes, settings without defects)
  6. `Returns & Replacement` (damaged on delivery, wrong items, return window)
  7. `Warranty Claims` (warranty registration, Kestrel Shield coverage, claim status)
* **Team Renaming Policy:** In accordance with Operations Policy §5 (effective 15 Jan 2026), `Installations` became `Installs & Demo`, and `Consumables` became `Filters & Consumables`.

---

## 2. Approach & Architecture

We built a **Hybrid Feature + Linear Support Vector Machine** pipeline:
* **Text Features:** Sublinear TF-IDF word n-grams (1, 3) + character n-grams within word boundaries (3, 5).
* **Intake Metadata:** One-hot encoded categorical features available at initial creation (`channel`, `product_family`, `warranty_status`).
* **Classifier:** 5-fold **Calibrated Linear Support Vector Classifier (LinearSVC)** (`C=1.0`), producing well-calibrated soft probability distributions across all 7 queues.
* **Leakage Prevention:** Strictly excluded downstream operational fields from `resolution_log.csv` (`first_team`, `final_team`, `transfers`, `resolved_at`) and ticket identifiers (`request_id`, `source`).

---

## 3. Validation Methodology & Measured Results

### Out-of-Time Contiguous Holdout Setup
Random train/test splits were rejected to prevent duplicate customer text leakage and mask temporal drift. We utilized a chronological split mimicking the hidden test structure:
* **Training Period:** Requests created 1 Apr 2025 through 31 Mar 2026 ($N = 8,687$).
* **Validation Period:** Requests created 1 Apr 2026 through 30 Jun 2026 ($N = 2,135$, Q2 2026).
* **Historical Backtest:** Trained through 31 Dec 2025, evaluated on 1 Jan 2026 – 31 Mar 2026 ($N = 2,168$, Q1 2026).

### Benchmark Comparison

| Candidate Model | Validation Accuracy | Validation Macro F1 | Errors (Count / %) |
| :--- | :---: | :---: | :---: |
| **A. Majority-Class Baseline (`Repairs`)** | 28.90% | 6.41% | 1,518 / 71.10% |
| **B. Metadata-Only Baseline (Logistic Regression)** | 34.99% | 13.40% | 1,388 / 65.01% |
| **C. Word TF-IDF (1,2) + Logistic Regression** | 93.91% | 93.94% | 130 / 6.09% |
| **D1. Word + Char TF-IDF + Logistic Regression** | 94.75% | 94.75% | 112 / 5.25% |
| **D2. Word + Char TF-IDF + LinearSVC** | 95.74% | 95.74% | 91 / 4.26% |
| **E1. Hybrid (Word+Char+Metadata) + LogReg** | 95.78% | 95.62% | 90 / 4.22% |
| **E2. Hybrid + Calibrated LinearSVC (CHOSEN)** | **96.58%** | **96.38%** | **73 / 3.42%** |
| **E3. Hybrid + Hard Rule Override Layer** | 93.44% | 93.35% | 140 / 6.56% |

### Key Validation Metrics (Chosen Model)
* **Primary Validation Accuracy:** **96.58%** (2,062 / 2,135 correct).
* **Secondary Validation Macro F1:** **96.38%**.
* **Deduplicated Out-of-Time Accuracy:** **96.31%** (Macro F1: **96.07%**) when excluding all repeated text strings appearing across the train/validation boundary.
* **Historical Backtest Accuracy:** **96.96%** (Macro F1: **96.70%**).

---

## 4. Why the Policy Hard-Rule Layer Was Rejected

We tested deterministic regex rules designed to disambiguate `Billing` from incidental payment mentions (e.g. "I paid for repair").
* **Empirical Result:** Applying the hard rule override caused validation accuracy to drop from **96.58% down to 93.44%**.
* **Reason:** Multi-token n-grams and calibrated SVM boundary weights already learn subtle contextual patterns more accurately than brittle regex heuristics. Hard overrides created false-positive reclassifications.
* **Decision:** Hard rule overrides were **REJECTED**. The final production pipeline relies on calibrated ML probabilities.

---

## 5. Expected Hidden-Test Performance

* **Estimated Score Range:** **96.0% – 96.5% Accuracy** (Point estimate: ~96.3%).
* **Primary Metric:** Multi-class Classification Accuracy against ground-truth routing.
* **Uncertainty Disclosure:** While supported by contiguous out-of-time holdouts and backtests, the actual score on the hidden test set remains an estimate and is unknown until final evaluation.

---

## 6. Business Impact & Financial Analysis

* **Stated Intake Volume:** ~700 requests/month = 8,400 requests/year.
* **Vendor Licence Avoided:** Up to **Rs 3,20,000 / year** (equivalent to **Rs 38.10 per request** at 8,400 requests/year) is potentially avoidable.
* **Inference API Cost:** **Rs 0** per prediction / **Rs 0** per month (100% local CPU execution, <0.5 ms latency). Local server/hosting costs depend on existing CRM server infrastructure and are not separately monetized.
* **Operational Misrouting Cost Consideration:** Under Policy §4 (Rs 565 per misrouted ticket), the model's 3.42% validation error rate corresponds to ~287 expected errors/year or approximately **Rs 1,62,000 / year** in operational handling. (This is an ongoing operational consideration rather than a claimed incremental savings, as the legacy bot's historical error rate is unmeasured).

---

## 7. Project Structure

```
kestrel_assessment/
├── README.md                   # Project documentation & operational guide
├── requirements.txt            # Python dependencies
├── memo.md                     # Non-technical 1-page memo for Ritu Deshpande
├── submission-form.md          # Completed Task 2 assessment submission form
├── evaluation_report.md        # Comprehensive benchmark & validation report
├── error_analysis.md           # Error taxonomy and failure case diagnosis
├── predictions.csv             # Test predictions matching sample_submission.csv
├── models/
│   └── kestrel_router_pipeline.joblib  # Saved trained model & feature vectorizers
├── src/
│   ├── preprocessing.py        # Mojibake text repair & canonical team mappings
│   ├── train.py                # Model training script
│   ├── predict.py              # Test set batch inference script
│   └── evaluate.py             # Out-of-time chronological validation runner
└── app/
    ├── main.py                 # FastAPI service with POST /predict & health checks
    ├── model.py                # Router model loader & reason explanation engine
    ├── schemas.py              # Pydantic request/response schemas
    └── static/
        ├── index.html          # Clean 1-screen interactive web UI
        ├── style.css           # Modern dark-mode styling
        └── app.js              # Frontend interactive logic and sample presets
```

---

## 8. Quickstart & Reproduction Guide

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Out-of-Time Validation Suite
```bash
python -m src.evaluate
```

### Step 3: Train Full Production Model
```bash
python -m src.train
```

### Step 4: Generate Test Predictions (`predictions.csv`)
```bash
python -m src.predict
```
*Executes automated checks verifying row count (2,178), column headers, exact request_id order, zero missing values, and strictly valid canonical 7 team names.*

### Step 5: Start the API Service & Interactive UI
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
* **Interactive UI:** Open [http://localhost:8000](http://localhost:8000)
* **API Documentation:** Open [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** `GET /health`
* **Prediction Endpoint:** `POST /predict`

---

## 9. API Example

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "request_text": "water purifier leaking water from bottom, paid for repair in full yesterday pls send technician",
    "product_family": "Water Purifier",
    "warranty_status": "in_warranty",
    "channel": "chat"
  }'
```

**Response:**
```json
{
  "request_id": null,
  "predicted_team": "Repairs",
  "confidence": 0.811,
  "reasons": [
    "Text evidence: water leakage / physical defect reported, breakdown / electrical trip reported.",
    "Context: Water Purifier request via CHAT under 'in_warranty' status.",
    "High statistical confidence (81.1%), clear separation over Filters & Consumables (16.3%)."
  ],
  "model_signal": "CalibratedLinearSVC | n-gram TF-IDF + Safe Metadata | P(Repairs)=0.8110",
  "probabilities": {
    "Billing": 0.0061,
    "Filters & Consumables": 0.1628,
    "Installs & Demo": 0.0057,
    "Product Advice": 0.0091,
    "Repairs": 0.811,
    "Returns & Replacement": 0.0035,
    "Warranty Claims": 0.0017
  }
}
```
