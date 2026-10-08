# Kestrel Service Request Router — Evaluation Report

## 1. Executive Summary
* **Task:** Replace the third-party vendor routing bot with an in-house local ML routing engine for Kestrel Home Appliances.
* **Target:** 7 canonical service queues (`Repairs`, `Billing`, `Filters & Consumables`, `Installs & Demo`, `Product Advice`, `Returns & Replacement`, `Warranty Claims`).
* **Validation Setup:** Contiguous Out-of-Time Holdout Split:
  * *Training Set:* 1 Apr 2025 – 31 Mar 2026 ($N = 8,687$ requests)
  * *Validation Set:* 1 Apr 2026 – 30 Jun 2026 ($N = 2,135$ requests)
* **Chosen Architecture:** Hybrid Feature Pipeline (Word n-grams (1,3) + Char_wb n-grams (3,5) + One-Hot Encoded Safe Metadata) with a 5-fold **Calibrated Linear Support Vector Classifier (LinearSVC)**.
* **Key Measured Metrics:**
  * **Validation Accuracy (Primary):** **96.58%** (2,062 / 2,135 correct; 73 errors / 3.42% error rate).
  * **Validation Macro F1 (Secondary):** **96.38%**.
  * **Deduplicated Validation Accuracy:** **96.31%** (Macro F1 96.07%) when excluding duplicate text strings appearing across the train/val split.
  * **Earlier Historical Backtest (Q1 2026):** **96.96%** (Macro F1 96.70%).
  * **Client Target Threshold:** Exceeds the client's $\ge 90.0\%$ requirement.

---

## 2. Validation Methodology & Leakage Prevention

### Validation Protocol
Standard random K-Fold cross-validation was rejected because:
1. It leaks repeated customer text strings between train and validation folds.
2. It masks operational drift (Zoho migration on 1 Oct 2025; team renaming on 15 Jan 2026).
3. The true evaluation task is predicting future Q3 2026 requests (`test_unlabelled.csv`).

We implemented an **out-of-time chronological validation split**:
* **Training Set:** Requests created between `2025-04-01 00:31` and `2026-03-31 21:50` ($N = 8,687$).
* **Holdout Validation Set:** Requests created between `2026-04-01 01:48` and `2026-06-30 23:33` ($N = 2,135$).
* **Backtest Set:** Trained through `2025-12-31` and evaluated on `2026-01-01` to `2026-03-31` ($N = 2,168$).

### Leakage Audit Summary
* **SAFE Features Included:** `request_text` (cleaned), `product_family`, `warranty_status`, `channel`.
* **EXCLUDED Features:**
  * `resolution_log.csv` (`first_team`, `final_team`, `transfers`, `resolved_at`): Downstream post-intake leakage.
  * `request_id`: Arbitrary identifier.
  * `source`: Legacy Zoho flag absent in future test data (100% CRM).

---

## 3. Candidate Benchmark Comparison

All models were evaluated on the exact same chronological validation holdout ($N = 2,135$):

| Candidate Model | Accuracy | Macro F1 | Errors (Count / %) |
| :--- | :---: | :---: | :---: |
| **A. Majority Class Baseline (`Repairs`)** | 28.90% | 6.41% | 1,518 / 71.10% |
| **B. Metadata-Only Baseline (Logistic Regression)** | 34.99% | 13.40% | 1,388 / 65.01% |
| **C. Word TF-IDF (1,2) + Logistic Regression** | 93.91% | 93.94% | 130 / 6.09% |
| **D1. Word (1,3) + Char (3,5) TF-IDF + LogReg** | 94.75% | 94.75% | 112 / 5.25% |
| **D2. Word (1,3) + Char (3,5) TF-IDF + LinearSVC** | 95.74% | 95.74% | 91 / 4.26% |
| **E1. Hybrid (Word+Char+Metadata) + LogReg** | 95.78% | 95.62% | 90 / 4.22% |
| **E2. Hybrid (Word+Char+Metadata) + Calibrated LinearSVC (CHOSEN)** | **96.58%** | **96.38%** | **73 / 3.42%** |
| **E3. Hybrid + Deterministic Hard-Rule Override Layer** | 93.44% | 93.35% | 140 / 6.56% |

---

## 4. Policy Rule Experimentation & Rejection
We tested deterministic operational rule layers designed to enforce `ops-policy.pdf` distinctions (e.g., forcing `Billing` only when payment keywords appear, and redirecting "paid for repair" complaints).
* **Finding:** Applying the hard regex rule layer dropped validation accuracy from **96.58% down to 93.44%**.
* **Reason:** Sublinear TF-IDF character and word n-grams implicitly learn multi-token contextual signals with fine-grained probability weighting. Rule overrides introduced crude boundary errors on ambiguous tickets.
* **Decision:** Hard rule overrides were **REJECTED**. The final production system relies strictly on the calibrated soft ML probabilities and does NOT use the hard rule override.

---

## 5. Per-Team Performance Breakdown (Chosen Model)

```
                       Precision    Recall  F1-Score   Support
              Billing     0.9673    0.9819    0.9745       331
Filters & Consumables     0.9420    0.9684    0.9550       285
      Installs & Demo     0.9614    0.9739    0.9676       230
       Product Advice     0.9596    0.9683    0.9640       221
              Repairs     0.9883    0.9579    0.9728       617
Returns & Replacement     0.9715    0.9484    0.9598       252
      Warranty Claims     0.9369    0.9698    0.9531       199

             Accuracy                         0.9658      2135
            Macro Avg     0.9610    0.9670    0.9638      2135
         Weighted Avg     0.9662    0.9658    0.9659      2135
```

### Confusion Matrix

```
True \ Pred            BIL   F&C   I&D   ADV   REP   R&R   WAR   Total
Billing                325     1     2     1     0     0     2     331
Filters & Consumables    1   276     1     2     2     1     2     285
Installs & Demo          2     1   224     2     0     1     0     230
Product Advice           2     3     0   214     0     0     2     221
Repairs                  6    10     2     3   591     1     4     617
Returns & Replacement    0     0     3     1     1   239     8     252
Warranty Claims          0     2     1     0     1     2   193     199
Total Predicted        336   293   233   223   595   244   211   2,135
```

---

## 6. Business Impact Analysis
* **Stated Intake Volume:** ~700 requests/month = 8,400 requests/year.
* **Vendor Licence Avoided:** Up to **Rs 3,20,000 / year** (Rs 38.10 per request at 8,400 requests/year) is potentially avoidable.
* **Inference API Cost:** **Rs 0** (fully local execution).
* **Operational Misrouting Cost:** Under Policy §4 (Rs 565 per misrouted ticket), the expected 287 model errors/year at 3.42% error rate represents an operational handling cost of approximately **Rs 1,62,000 / year**. (This is an ongoing operational consideration; net savings cannot be claimed without knowing the vendor bot's historical error rate).

---

## 7. Expected Hidden-Test Performance
* **Estimated Accuracy Range:** **96.0% – 96.5%** (Point estimate: ~96.3%).
* **Validation Basis:** Supported by 96.58% out-of-time validation, 96.31% deduplicated validation, and 96.96% Q1 2026 backtest.
* **Uncertainty Disclosure:** The actual score on the hidden test set remains unknown until formal evaluation.
