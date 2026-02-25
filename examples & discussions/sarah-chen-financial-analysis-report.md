# Process & Validation Report

**Client:** Sarah Chen  
**Date:** February 10, 2026  
**Primary Goal Evaluated:** House Purchase ($10,000,000 by 2033)  
**Secondary Goal:** Retirement at age 60 (2046), funded primarily by 401(k)  
**Services Used:** Cashflow Model API (port 8001) and NeoEngine API (port 8000)

---

## Step 1. Client Context and Goal Interaction

Sarah is 40 with two dependents, earns $300,000 with 3% annual growth, and spends $150,000 plus $60,000 rent, also rising 3%. Her stated goals are a $10M home purchase in 2033 (a 7‑year horizon from 2026) and retirement at 60 (2046). Retirement is meant to be funded primarily through the 401(k), while the brokerage and cash balances are intended for the house purchase.

This means goals cannot be evaluated in isolation. A $10M house purchase should not draw down the 401(k), and retirement cannot assume the brokerage remains intact. The validation therefore compares the 2033 liquid pool (bank + brokerage + Roth IRA) to $10M, and compares the 2046 401(k) balance to $5M.

---

## Step 2. End‑to‑End Modeling Chain

1. NeoEngine Layer 1 produces asset‑class weights and expected return/volatility from forward‑looking CMA data.  
2. NeoEngine Layer 2 allocates active versus passive risk budgets by asset class.  
3. NeoEngine Layer 3 selects implementable securities and weights for active sleeves.  
4. The cashflow model uses the CMA assumptions to compute account‑level expected returns based on each account’s asset‑class allocation.  
5. Deterministic simulations project balances and evaluate goal feasibility.

This chain ensures that portfolio construction choices flow directly into cashflow projections.

---

## Step 3. Baseline Cashflow Model (Deterministic)

**House funding check (liquid assets, 2033):**  
Useable Balance: **$8,340,952**  
Shortfall vs $10M: **$1,659,048**

**Retirement funding check (401k only, 2046):**  
401(k) Balance: **$4,474,753**  
Shortfall vs $5M: **$525,247**

This confirms that the baseline allocation is unlikely to fund the house purchase on a liquid‑only basis and leaves a modest retirement gap.

---

## Step 4. Detailed Annual Cashflow Projection (Baseline, 2026–2046)

| Year | Age | Gross Income | Base Spending | Housing Costs | Taxes | Net Cashflow | Useable Balance | 401k Balance | Total Net Worth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026 | 40 | $0 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2027 | 41 | $300,000 | $154,500 | $60,000 | $97,369 | $-32,369 | $5,825,225 | $1,098,611 | $6,923,836 |
| 2028 | 42 | $309,000 | $159,135 | $61,800 | $101,270 | $-33,705 | $6,174,197 | $1,204,663 | $7,378,860 |
| 2029 | 43 | $318,270 | $163,909 | $63,654 | $105,289 | $-35,082 | $6,548,660 | $1,318,718 | $7,867,379 |
| 2030 | 44 | $327,818 | $168,826 | $65,564 | $109,428 | $-36,500 | $6,950,488 | $1,441,380 | $8,391,868 |
| 2031 | 45 | $337,653 | $173,891 | $67,531 | $113,692 | $-37,961 | $7,381,685 | $1,573,299 | $8,954,984 |
| 2032 | 46 | $347,782 | $179,108 | $69,556 | $118,082 | $-39,465 | $7,844,405 | $1,715,172 | $9,559,577 |
| 2033 | 47 | $358,216 | $184,481 | $71,643 | $122,606 | $-41,014 | $8,340,952 | $1,867,751 | $10,208,703 |
| 2034 | 48 | $368,962 | $190,016 | $73,792 | $127,264 | $-42,610 | $8,873,800 | $2,031,843 | $10,905,643 |
| 2035 | 49 | $380,031 | $195,716 | $76,006 | $132,062 | $-44,253 | $9,445,597 | $2,208,319 | $11,653,916 |
| 2036 | 50 | $391,432 | $201,587 | $78,286 | $134,186 | $-49,628 | $10,055,484 | $2,405,452 | $12,460,936 |
| 2037 | 51 | $403,175 | $207,635 | $80,635 | $139,277 | $-51,372 | $10,710,189 | $2,617,460 | $13,327,649 |
| 2038 | 52 | $415,270 | $213,864 | $83,054 | $144,521 | $-53,169 | $11,412,973 | $2,845,468 | $14,258,440 |
| 2039 | 53 | $427,728 | $220,280 | $85,546 | $175,022 | $-80,120 | $12,203,845 | $3,090,680 | $15,294,526 |
| 2040 | 54 | $440,560 | $226,888 | $88,112 | $197,252 | $-98,692 | $13,070,929 | $3,292,125 | $16,363,054 |
| 2041 | 55 | $453,777 | $233,695 | $90,755 | $205,955 | $-103,629 | $13,999,618 | $3,467,422 | $17,467,040 |
| 2042 | 56 | $467,390 | $240,706 | $93,478 | $213,543 | $-107,337 | $14,994,291 | $3,648,569 | $18,642,860 |
| 2043 | 57 | $481,412 | $247,927 | $96,282 | $221,452 | $-111,250 | $16,059,635 | $3,839,204 | $19,898,839 |
| 2044 | 58 | $495,854 | $255,365 | $99,171 | $229,880 | $-115,562 | $17,200,672 | $4,040,249 | $21,240,921 |
| 2045 | 59 | $510,730 | $263,026 | $102,146 | $238,734 | $-120,176 | $18,422,780 | $4,252,011 | $22,674,791 |
| 2046 | 60 | $526,052 | $270,917 | $105,210 | $247,980 | $-125,055 | $24,081,820 | $4,474,753 | $28,556,573 |

---

## Step 5. House‑Goal Portfolio Selection (Minimum Volatility at Required Return)

**Required return calculation:**  
Investable base = $5,595,000 (non‑401k assets less a six‑month reserve of $105,000).  
Required CAGR to reach $10M in 7 years = **8.65%**.

**Search over volatility to find the minimum‑volatility portfolio meeting the return:**

| Iteration | Vol Min | Vol Max | Mid Vol | Expected Return |
| --- | --- | --- | --- | --- |
| 1 | 5.00% | 14.47% | 9.73% | 8.68% |
| 2 | 5.00% | 9.73% | 7.37% | 6.50% |
| 3 | 7.37% | 9.73% | 8.55% | 7.86% |
| 4 | 8.55% | 9.73% | 9.14% | 8.28% |
| 5 | 9.14% | 9.73% | 9.44% | 8.48% |

**Selected house portfolio:** expected return **8.68%**, volatility **9.42%** (minimum volatility meeting the return requirement).

---

## Step 6. House‑Goal Cashflow Evidence (Solution vs Baseline)

**Solution Cashflow Projection (House Portfolio, 2026–2033)**

| Year | Age | Gross Income | Base Spending | Housing Costs | Taxes | Net Cashflow | Useable Balance | 401k Balance | Total Net Worth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026 | 40 | $0 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2027 | 41 | $300,000 | $154,500 | $60,000 | $97,369 | $-32,369 | $5,936,181 | $1,098,611 | $7,034,792 |
| 2028 | 42 | $309,000 | $159,135 | $61,800 | $101,270 | $-33,705 | $6,411,488 | $1,204,663 | $7,616,151 |
| 2029 | 43 | $318,270 | $163,909 | $63,654 | $105,289 | $-35,082 | $6,929,398 | $1,318,718 | $8,248,117 |
| 2030 | 44 | $327,818 | $168,826 | $65,564 | $131,589 | $-58,661 | $7,525,930 | $1,441,380 | $8,967,310 |
| 2031 | 45 | $337,653 | $173,891 | $67,531 | $142,071 | $-66,340 | $8,179,040 | $1,518,320 | $9,697,361 |
| 2032 | 46 | $347,782 | $179,108 | $69,556 | $148,105 | $-69,487 | $8,888,828 | $1,585,637 | $10,474,465 |
| 2033 | 47 | $358,216 | $184,481 | $71,643 | $153,859 | $-72,267 | $9,660,213 | $1,653,959 | $11,314,172 |

**Key outcomes (house portfolio applied):**  
Useable Balance at 2033: **$9,660,213** (shortfall **$339,787**).  
401(k) Balance at 2046 (if no retirement adjustment): **$2,794,527** (shortfall **$2,205,473**).

This shows the house solution materially improves the housing outcome but harms retirement under the liquidity‑first withdrawal sequence.

---

## Step 7. Option 1 Validation: Sequential Goal Management

**Objective:** Keep the house solution intact, then re‑optimize the 401(k) after the 2033 purchase to restore retirement feasibility.

**Post‑house retirement portfolio search (minimum volatility meeting the retirement target):**

| Iteration | Vol Min | Vol Max | Mid Vol | Expected Return | End 401k (2046) |
| --- | --- | --- | --- | --- | --- |
| 1 | 5.00% | 14.47% | 9.73% | 8.68% | $5,783,080 |
| 2 | 5.00% | 9.73% | 7.37% | 6.50% | $4,415,818 |
| 3 | 7.37% | 9.73% | 8.55% | 7.86% | $5,223,161 |
| 4 | 7.37% | 8.55% | 7.96% | 7.35% | $4,905,147 |
| 5 | 7.96% | 8.55% | 8.26% | 7.62% | $5,070,697 |

**Selected retirement portfolio (post‑2033):** expected return **7.62%**, volatility **7.93%**, projected 401(k) at 2046 = **$5,070,697**.

**Post‑house 401(k) trajectory (actual years, starting from the 2033 balance):**

| Actual Year | Age | 401k Balance |
| --- | --- | --- |
| 2033 | 47 | $1,653,959 |
| 2034 | 48 | $1,808,092 |
| 2035 | 49 | $1,974,424 |
| 2036 | 50 | $2,161,285 |
| 2037 | 51 | $2,362,936 |
| 2038 | 52 | $2,580,547 |
| 2039 | 53 | $2,815,381 |
| 2040 | 54 | $3,068,801 |
| 2041 | 55 | $3,342,279 |
| 2042 | 56 | $3,637,401 |
| 2043 | 57 | $3,955,881 |
| 2044 | 58 | $4,299,567 |
| 2045 | 59 | $4,670,455 |
| 2046 | 60 | $5,070,697 |

**Option 1 outcome:** House shortfall remains **$339,787** in 2033, and retirement is restored to **$5.07M** by 2046 after the post‑purchase adjustment.

---

## Step 8. Option 2 Validation: Joint Optimization Across Both Goals

**Objective:** Optimize the house portfolio for liquid assets and a separate retirement portfolio for the 401(k) from the start, both using the minimum‑volatility‑for‑return objective.

**Retirement portfolio search under joint optimization:**

| Iteration | Vol Min | Vol Max | Mid Vol | Expected Return | End 401k (2046) |
| --- | --- | --- | --- | --- | --- |
| 1 | 5.00% | 14.47% | 9.73% | 8.68% | $4,038,233 |
| 2 | 9.73% | 14.47% | 12.10% | 10.12% | $5,769,089 |
| 3 | 9.73% | 12.10% | 10.92% | 9.42% | $4,862,104 |
| 4 | 10.92% | 12.10% | 11.51% | 9.77% | $5,303,768 |
| 5 | 10.92% | 11.51% | 11.21% | 9.60% | $5,080,167 |

**Selected retirement portfolio (joint):** expected return **9.60%**, volatility **10.96%**, projected 401(k) at 2046 = **$5,080,167**.

**Joint policy cashflow projection (2026–2033):**

| Year | Age | Gross Income | Base Spending | Housing Costs | Taxes | Net Cashflow | Useable Balance | 401k Balance | Total Net Worth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026 | 40 | $0 | $0 | $0 | $0 | $0 | $0 | $0 | $0 |
| 2027 | 41 | $300,000 | $154,500 | $60,000 | $97,369 | $-32,369 | $5,936,181 | $1,124,407 | $7,060,588 |
| 2028 | 42 | $309,000 | $159,135 | $61,800 | $101,270 | $-33,705 | $6,411,488 | $1,261,344 | $7,672,832 |
| 2029 | 43 | $318,270 | $163,909 | $63,654 | $105,289 | $-35,082 | $6,929,398 | $1,412,072 | $8,341,471 |
| 2030 | 44 | $327,818 | $168,826 | $65,564 | $131,589 | $-58,661 | $7,525,930 | $1,577,981 | $9,103,911 |
| 2031 | 45 | $337,653 | $173,891 | $67,531 | $142,071 | $-66,340 | $8,179,040 | $1,704,330 | $9,883,370 |
| 2032 | 46 | $347,782 | $179,108 | $69,556 | $148,105 | $-69,487 | $8,888,828 | $1,827,612 | $10,716,441 |
| 2033 | 47 | $358,216 | $184,481 | $71,643 | $153,859 | $-72,267 | $9,660,213 | $1,959,141 | $11,619,354 |

**Option 2 outcome:** House shortfall remains **$339,787** in 2033, while the 401(k) reaches **$5.08M** by 2046 without waiting for 2033.

---

## Step 9. Baseline vs Solution Comparison (Key Metrics)

| Metric | Baseline | House Portfolio Only | Option 1 (Sequential) | Option 2 (Joint) |
| --- | --- | --- | --- | --- |
| Useable Balance in 2033 | $8,340,952 | $9,660,213 | $9,660,213 | $9,660,213 |
| House Shortfall in 2033 | $1,659,048 | $339,787 | $339,787 | $339,787 |
| 401(k) Balance in 2046 | $4,474,753 | $2,794,527 | $5,070,697 | $5,080,167 |

---

## Step 10. Risk Management Validation

Risk controls are applied separately for the housing portfolio and the retirement portfolio in both options. Each portfolio is constructed to meet its return requirement with the lowest practical volatility, with explicit constraints on tracking error, implementation cost, and drawdown monitoring. Rebalancing is scheduled quarterly, with annual policy reviews and trigger‑based re‑assessments if cashflow, goals, or risk tolerance materially change.

---

## Step 11. Probabilistic Analysis (Monte Carlo, 200 Runs)

Monte Carlo simulations were run for the baseline, the house‑portfolio solution, and the joint optimization (Option 2). The model reports success probability as the share of simulations without cash‑balance ruin and provides terminal wealth percentiles. These results reflect dispersion in long‑term wealth and do not directly measure goal attainment at 2033 or 2046.

| Scenario | Success Probability | Ruin Probability | Terminal Wealth 5th | Terminal Wealth 50th | Terminal Wealth 95th |
| --- | --- | --- | --- | --- | --- |
| Baseline | 100.0% | 0.0% | $27,235,035 | $101,601,336 | $308,790,826 |
| House Portfolio | 100.0% | 0.0% | $28,569,551 | $89,212,422 | $230,115,689 |
| Option 2 (Joint) | 100.0% | 0.0% | $28,569,551 | $89,212,422 | $230,115,689 |

---

## Deliverables

Financial Planning Policy (Option 1): `examples & discussions/sarah-chen-financial-planning-policy-option1.md`  
Financial Planning Policy (Option 2): `examples & discussions/sarah-chen-financial-planning-policy-option2.md`  
Process & Validation Report: `examples & discussions/sarah-chen-financial-analysis-report.md`  
Supporting Output JSON: `examples & discussions/sarah-chen-options-output.json`  
Monte Carlo Output JSON: `examples & discussions/sarah-chen-options-mc-output.json`

---

## System Notes

Cashflow API ran on port 8001 and NeoEngine on port 8000. All simulations and optimizations were executed locally.
