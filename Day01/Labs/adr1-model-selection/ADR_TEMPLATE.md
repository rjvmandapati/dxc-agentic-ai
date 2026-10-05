# ADR-001 — ClaimsCopilot: model and deployment decision

| | |
|---|---|
| **Version** | v1 *(change to v2 in the second file)* |
| **Status** | Proposed |
| **Author** | *your name* · Team *x* |
| **Date** | *today* |

> **What changed and why** *(v2 only — delete this box in v1)*
> *2–3 lines: what the update was, and which parts of this ADR you changed.*

---

## 1. Context
*Two or three lines in your own words: what problem, for whom, and the main constraints (data, budget, skills, timeline).*
The management of Bharat Suraksha Insurance wants to have a ClaimsCoPilot that helps with summarizing the Claims file, answer thousands of questions coming from customers and process letters to customers in English and Hindi within a minute.
## 2. Decision drivers
*Rank the top 4. Examples: data residency · cost per month · time to launch · quality · team skills · latency · vendor lock-in.*

1. Data residency (privacy and security)
2. Cost per month
3. Latency (response times)
4. Quality
5. Ease of use

## 3. Options considered

| Option (path + pay model + model) | Pros | Cons |
|---|---|---|
| **A.** |Public cloud | |
| **B.** | | |
| **C.** | | |

## 4. Decision
**We will use** *(path)* **with** *(pay model)* **and** *(model(s) per workload)* **in** *(region)* **because** *(top 2 reasons)*.

| Workload | Model | Why |
|---|---|---|
| 1 · Claim summary | | |
| 2 · Policy Q&A | | |
| 3 · Customer letters | | |

## 5. Data residency & protection
*Region, private connectivity, who can see prompts, what is logged.*

## 6. Cost estimate (per month)

| Workload | Calculation | USD / month |
|---|---|---|
| 1 · Summary | | |
| 2 · Q&A | | |
| 3 · Letters | | |
| **Total** | | |

*Fits the USD 4,000 budget?* Yes / No — *what would you do about it?*

## 7. Consequences
- **Easier:**
- **Harder:**
- **Risks and how we reduce them:**
- **How we change our mind later (exit plan):**

## 8. Rejected options — in one line each
-
-
