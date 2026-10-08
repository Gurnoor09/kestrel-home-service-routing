# Kestrel Service Request Router — Error Analysis Report

## 1. Overview of Validation Errors
Across the 2,135 out-of-time validation requests (Q2 2026), the **Calibrated LinearSVC** model produced **73 errors** (overall error rate: **3.42%**; accuracy: **96.58%**).

Rather than treating all discrepancies uniformly, this analysis categorizes errors into three distinct operational sources:
1. **Historical Routing Inconsistencies / Rerouting Cases:** Situations where the historical vendor bot made an intake assignment that conflicts with operational policy or downstream resolution outcomes.
2. **Genuinely Ambiguous Customer Requests:** Short, multi-intent, or underspecified messages lacking sufficient context for deterministic single-queue routing.
3. **Model Errors:** Cases where clear customer signals were misinterpreted by the classifier.

---

## 2. Top Confusion Pairs

| Rank | True Queue | Predicted Queue | Error Count | Primary Driver |
| :---: | :--- | :--- | :---: | :--- |
| **1** | **`Repairs`** | **`Filters & Consumables`** | **10** | Water purifier leak/breakdown complaints containing consumable words. |
| **2** | **`Returns & Replacement`** | **`Warranty Claims`** | **8** | Return requests mentioning warranty card registration or policy terms. |
| **3** | **`Repairs`** | **`Billing`** | **6** | Customer complaints stating "already paid in full" without stating symptoms. |
| **4** | **`Repairs`** | **`Warranty Claims`** | **4** | Customer requests opening with "warranty claim" but describing noisy machines. |
| **5** | **`Product Advice`** | **`Filters & Consumables`** | **3** | Spare parts compatibility queries without direct purchase intent. |
| **6** | **`Returns & Replacement`** | **`Installs & Demo`** | **3** | Requests stating product was delivered but uninstalled/missing items. |

---

## 3. Deep Dive into Key Error Categories

### A. Genuinely Ambiguous & Multi-Intent Customer Requests
* **Representative Examples:**
  * `SR509131`: `"hi, warranty card for mixer not registered, wrong model of mixer delivered very disappointed"` $\rightarrow$ True: `Returns & Replacement`, Pred: `Warranty Claims` (conf: 0.60).
  * `SR510179`: `"namaste, warranty card for machine not registered, cancel and return machine order KO2611815 pls call back"` $\rightarrow$ True: `Returns & Replacement`, Pred: `Warranty Claims` (conf: 0.52).
  * `SR509146`: `"hi, ceiling fan query already paid in full reg no SR42126"` $\rightarrow$ True: `Repairs`, Pred: `Billing` (conf: 0.71).
* **Analysis:** In these cases, the customer presents two simultaneous intents (e.g. warranty card registration AND delivery issue) or mentions payment status without providing any breakdown symptom. In real operations, human agents often require customer clarification for such tickets.

---

### B. Historical Routing Inconsistencies / Rerouting Cases
* **Representative Examples:**
  * `SR509030`: `"motor of purifier burnt smell"` $\rightarrow$ True: `Product Advice`, Pred: `Repairs` (conf: 0.97).
  * `SR510236`: `"induction cooktop showing error code E2 kindly resolve"` $\rightarrow$ True: `Product Advice`, Pred: `Repairs` (conf: 0.98).
* **Analysis:** A burnt motor smell and error code E2 are unambiguously hardware breakdown symptoms under Policy §3. The historical bot assigned these to `Product Advice`, which downstream agents would have had to transfer to `Repairs`. The ML model correctly identifies the repair intent, but is marked incorrect against the flawed historical bot label.

---

### C. Model Errors (N-gram Weight Misallocations)
* **Representative Examples:**
  * `SR508723`: `"water purifier leaking water from bottom reg no SR46774 purifier not working"` $\rightarrow$ True: `Repairs`, Pred: `Filters & Consumables` (conf: 0.99).
  * `SR509003`: `"purifier showing error code E3 purifier not working"` $\rightarrow$ True: `Repairs`, Pred: `Filters & Consumables` (conf: 0.98).
* **Analysis:** Because water purifier requests have high historical frequency in the consumables queue, the purifier-related n-grams occasionally overpower breakdown tokens when phrase length is short.

---

## 4. Operational Mitigations
1. **Calibrated Confidence Thresholding:** Requests with prediction confidence below 75% (~4% of volume) should be flagged for supervisor triage rather than routed blindly.
2. **Deterministic Pre-checks vs. Soft Probabilities:** While hard regex overrides hurt overall accuracy (dropping accuracy from 96.58% to 93.44%), the model's soft probabilities surface close second-ranked queues for human supervisor review.
