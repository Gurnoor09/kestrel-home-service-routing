# Kestrel Home Appliances — Task 2 Submission Form

## 1. Candidate & Project Information
* **Candidate Name / ID:** Candidate Submission (Variant B)
* **Target Project:** Kestrel Home Appliances — Service Request Intelligent Router (Task 2)
* **Date of Submission:** 8 October 2026
* **Honest Hours Spent:** `[PLACEHOLDER: Honest hours spent on assessment]`
* **Github Repository Link:** `[PLACEHOLDER: Github repo link]`
* **Public Google Drive Link:** `[PLACEHOLDER: Public Google Drive link]`
* **Screen Recording Link:** `[PLACEHOLDER: Screen recording link]`

---

## 2. Model & Performance Summary
* **Chosen Model Architecture:** Hybrid N-Gram TF-IDF (Word 1-3 grams + Char_wb 3-5 grams, sublinear TF) + One-Hot Encoded Intake Metadata (`product_family`, `warranty_status`, `channel`) with a 5-Fold **Calibrated Linear Support Vector Classifier (LinearSVC)**.
* **Primary Validation Strategy:** Contiguous Out-of-Time Chronological Holdout Split:
  * *Training Set:* 1 Apr 2025 – 31 Mar 2026 ($N = 8,687$ requests)
  * *Validation Set:* 1 Apr 2026 – 30 Jun 2026 ($N = 2,135$ requests)
* **Primary Validation Accuracy:** **96.58%** (2,062 / 2,135 correct; 73 errors / 3.42% error rate).
* **Secondary Validation Macro F1:** **96.38%**.
* **Deduplicated Out-of-Time Accuracy:** **96.31%** (Macro F1: **96.07%**) when excluding all exact duplicate texts appearing across the train/validation boundary.
* **Earlier Historical Backtest (Q1 2026):** **96.96%** (Macro F1: **96.70%**).
* **Output Predictions File:** `predictions.csv` ($N = 2,178$ rows, strictly canonical 7 team labels matching `sample_submission.csv` format and ID order).

---

## 3. Expected Score on Hidden Outcomes
* **Predicted Score Range:** **96.0% – 96.5% Accuracy** (Point estimate: ~96.3%).
* **Primary Metric:** Multi-class Classification Accuracy (Client requirement: $\ge 90.0\%$).
* **Secondary Metric:** Macro-averaged F1 Score (Estimated: **95.8% – 96.4%**).
* **Exact Validation Basis:**
  1. Primary out-of-time evaluation on Q2 2026 ($N=2,135$) measured **96.58%**.
  2. The deduplicated validation subset measured **96.31%**.
  3. Q1 2026 historical backtest measured **96.96%**.
  4. The final model was retrained on 100% of historical labelled data ($N=10,822$), expanding feature representation for Q3 2026 test inference.
* **Defensibility & Uncertainty Disclosure:** The contiguous out-of-time validation setup directly replicates the temporal nature of the Q3 2026 test set while strictly avoiding downstream leakage. However, the exact hidden test score remains unknown until evaluation on the unlabelled set is completed.

---

## 4. Scope, Pushbacks, and Client Alignment
* **Did you change, narrow, or push back on the client's ask?**
  * **Yes, on Label Mapping and Rule Overrides:**
    1. *Unified Canonical Target Labels:* Pre-Jan 15, 2026 records used `Installations` and `Consumables`. In accordance with Operations Policy §5, we mapped these to the active canonical teams (`Installs & Demo` and `Filters & Consumables`), ensuring test predictions adhere 100% to the post-renaming team structure.
    2. *Rejection of Hard Rule Overrides:* We experimented with deterministic regex rules to separate Billing from incidental payment mentions. While conceptually intuitive, hard rule overrides degraded validation accuracy from **96.58% down to 93.44%**. We therefore pushed back on hard deterministic overrides and retained the pure calibrated soft ML classifier.

---

## 5. Data Quality Audit & Identified Data Issues
* **What is wrong with what was handed to us in the data pack?**
  1. **Legacy Zoho Mojibake / Character Corruption:** Exactly 480 training records from legacy Zoho desk (pre-Oct 2025) contained corrupted UTF-8 byte sequences (e.g. `urgÃ©nt`, `smÃ©ll`, `paymÃ©nt`, `thÃ©`). We built automated text repair into the preprocessing pipeline.
  2. **Historical Routing Inconsistencies / Label Ambiguities:** In 89 instances, identical customer text was assigned to different teams historically, establishing ~1-2% baseline inconsistency in historical logs.
  3. **Zoho Timestamp Timezone Issue:** Legacy Zoho resolution times were imported in UTC without conversion to IST (§9 ops-policy), creating apparent duration anomalies in historical resolution logs.
  4. **Post-Intake Resolution Leakage:** `resolution_log.csv` contains post-intake operational outcomes (`transfers`, `final_team`, `resolved_at`). These were strictly excluded from model training and inference.
  5. **Covariate Shift on System Source:** Training contains 39.9% `legacy_zoho`, whereas test is 100% `crm`. `source` was excluded as a predictive feature to prevent out-of-distribution bias.

---

## 6. Business Case & ROI Analysis
* **Stated Intake Volume:** Approximately 700 requests/month = 8,400 requests/year.
* **Current Vendor Licence Cost:** Rs 3,20,000 / year (equivalent to **Rs 38.10 per request** at 8,400 requests/year).
* **Vendor Cost Avoided:** Up to **Rs 3,20,000 / year** is potentially avoidable by retiring the vendor licence.
* **Inference API Cost:** **Rs 0 per prediction** (Rs 0 / month) because inference runs fully locally. Local server compute/hosting costs depend on existing CRM infrastructure and are not separately monetized.
* **Operational Misrouting Cost Consideration:**
  * Policy §4 defines a Rs 565 penalty per misrouted ticket (Rs 305 handling transfer + Rs 260 extra customer contact).
  * At the model's 3.42% validation error rate, expected misroutes at 8,400 requests/year total approximately 287 requests, corresponding to an operational handling cost of approximately **Rs 1,62,000 / year**.
  * *(We do not know the incumbent vendor bot's historical error rate, so its avoided misrouting cost cannot be calculated; model misrouting remains an ongoing operational cost rather than a net savings claim).*

---

## 7. AI Tooling & Development Disclosure
* **AI Coding Assistants Used:** Advanced Agentic Coding Assistant during development for exploratory data analysis scripts, pipeline scaffolding, and interface styling.
* **Runtime Independence:** The trained model, API service, and prediction pipeline execute 100% locally with zero external API calls or third-party model dependencies.
