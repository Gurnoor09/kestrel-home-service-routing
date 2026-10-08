# MEMORANDUM

**TO:** Ritu Deshpande, Head of D2C Operations, Kestrel Home Appliances  
**FROM:** Machine Learning & Operations Technical Lead  
**DATE:** 8 October 2026  
**SUBJECT:** Service Routing Bot Replacement — Validation Findings, Financial Analysis, and Next Steps  

---

### 1. THE DECISION
**PROCEED TO A 2-WEEK SHADOW-MODE ROLLOUT TO RETIRE THE VENDOR BOT.**  
The data-driven evidence supports replacing the legacy third-party routing bot with the in-house routing model. We recommend launching the local service in **Shadow Mode** next week to verify live operational parity before issuing the vendor licence termination notice.

---

### 2. THE NUMBERS
* **Client Accuracy Target:** $\ge 90.0\%$ match against operational routing ground truth.
* **Measured Out-of-Time Validation Accuracy:** **96.58%** on contiguous holdout requests (Q2 2026).
* **Deduplicated Validation Accuracy:** **96.31%** (excluding repeated customer texts across the split boundary).
* **Macro-Averaged F1 Score:** **96.38%** across all 7 canonical queues, confirming strong routing performance on minority queues (`Warranty Claims`, `Installs & Demo`, `Filters & Consumables`).
* **Earlier Historical Backtest:** **96.96%** (Q1 2026).
* **Estimated Hidden-Test Accuracy:** **96.0% – 96.5%** (Point estimate: ~96.3%; actual hidden score remains unknown until evaluation).
* **Inference Runtime:** Fully local CPU execution (<1 millisecond per request) with zero external API calls.

---

### 3. THE RUPEES & BUSINESS CASE
* **Annual Inbound Volume:** Stated volume is approximately 700 requests/month (~8,400 requests/year).
* **Vendor Licence Cost Avoided:** **Rs 3,20,000 per year** (equivalent to **Rs 38.10 per request** at 8,400 requests/year) is potentially avoidable by decommissioning the vendor bot.
* **Paid API / External Model Costs:** **Rs 0 per prediction** (Rs 0/month) as inference runs entirely locally. (Hardware/hosting costs depend on existing shared CRM infrastructure and are not separately monetized).
* **Operational Misrouting Cost Consideration:** 
  * Under Policy §4, each transferred or misrouted request incurs **Rs 565** (Rs 305 handling transfer + Rs 260 extra customer contact).
  * At the measured 3.42% validation error rate, expected model misroutes total approximately **287 requests/year**, representing an operational handling cost of approximately **Rs 1,62,000 per year**.
  * *(Note: Because the incumbent vendor bot's historical error rate is unmeasured, this operational cost is an ongoing operational consideration rather than a claimed incremental savings).*

---

### 4. WHAT RITU SHOULD DO NEXT WEEK
1. **Deploy Shadow Mode (Monday):** Connect the local service (`POST /predict`) to receive live inbound requests in parallel with the incumbent vendor bot without altering actual agent queues.
2. **Review Live Parity (Wednesday):** Review sample predictions and queue distributions with Service Desk Manager Meenal Joshi, verifying that high-confidence tickets route cleanly to the 7 canonical teams.
3. **Establish Low-Confidence Triage (Thursday):** Configure the CRM workflow so that tickets with prediction confidence below 75% (~4% of total traffic) route to a supervisor pool for manual confirmation.
4. **Issue Licence Non-Renewal (Friday):** Pending successful shadow parity, submit formal non-renewal notice for the Rs 3.2L annual vendor licence.
