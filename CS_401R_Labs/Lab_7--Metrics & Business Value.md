# Lab 7: Metrics + Economics & Business Value

**Assigned:** Thu Nov 19 | **Due:** Tue Dec 1, midnight *(Tuesday exception — see syllabus)*
**Chapters:** *Metrics, Benchmarks & Guardrails*, *AI Economics*, *Measuring Business Value*
**Builds on:** Labs 1–6 — measures the value and cost of the platform you built

## Objective

The NorthStar platform is live. Now answer the question every CFO and CDO will ask: *is it worth it?*

This lab builds the measurement infrastructure to answer that question rigorously — a metric pyramid, unit economics computed from your own measured usage, and an executive scorecard that traces from model outputs to business outcomes. Every number you produce must be derived from something you or the reference implementation actually observed. **Invented figures score zero even when they are plausible.**

Governance and closing-the-loop content is addressed in the team project. This lab is economics and value measurement.

## Starter Kit

**None.** Labs 5–7 have no starter kit. Lab 7 consumes what Labs 1–6 produced.

## Read This First — Cost

**Lab 7 is the cheapest lab in the course, and the only one with no infrastructure to tear down.**

It requires no endpoint, no processing job, no Glue run, and no Terraform apply. Every AWS call in this lab is read-only.

| Call | Rate | This lab's usage |
|---|---|---|
| `aws pricing get-products` | **free** | ~10 calls |
| `aws ce get-cost-and-usage` | **$0.01 per request** | ~5 calls = **$0.05** |
| `aws cloudwatch get-metric-statistics` | $0.01 per 1,000 | negligible |

**Total expected spend: under $0.10.** If you find yourself launching an instance in Lab 7, stop — you have misread a task.

There is no teardown script for this lab because there is nothing to tear down. There *is* still a teardown gate, and it is inherited: see **Teardown** at the end.

## Read This Second — Your AWS Bill Is Not Your Cost

Before you start, understand the single most important fact in this lab.

The reference account ran **all of Labs 1 through 6** during July 2026 — Feature Store ingestion, Glue ETL and crawlers, three SageMaker endpoints across three instance families, model-monitoring processing jobs, CodeBuild, a NAT gateway, KMS, CloudWatch alarms and custom metrics. Cost Explorer reports the following for that month:

| Service | Measured usage | Billed |
|---|---|---|
| SageMaker Hosting `ml.m5.large` | 0.5889 hr | **$0.00** |
| SageMaker Hosting `ml.t2.medium` | 0.4328 hr | **$0.00** |
| SageMaker Hosting `ml.m6g.large` | 0.0192 hr | **$0.00** |
| SageMaker Processing `ml.t3.large` | 0.0958 hr | **$0.00** |
| SageMaker Processing `ml.t3.medium` | 0.2283 hr | **$0.00** |
| Glue ETL | 1.0311 DPU-hr | **$0.00** |
| Glue Crawler | 0.4786 DPU-hr | **$0.00** |
| Feature Store writes | 7,967 request units | **$0.00** |
| S3 requests | 764 PUT / 3,260 GET | **$0.00** |
| NAT Gateway | 4 hr | **$0.00** |
| CodeBuild | 10 build-minutes | **$0.00** |
| **Whole account, whole month** | | **$0.00** |

Free tier absorbed the entire platform. **Your bill will look the same, and it will teach you nothing.**

This is not a quirk of a course account. It is the ordinary condition of every pilot AI system inside a large enterprise: the workload runs on committed capacity, an enterprise agreement, a shared account, or credits, and the invoice line that would tell you what it costs does not exist. Meanwhile the same system at production scale is a real budget line that someone has to defend.

**So the rule for this lab, and for the rest of your career:**

> **Unit economics are computed from `usage × published rate`. Never from the invoice.**
> The invoice tells you what you were charged. The rate card tells you what you consumed. Only the second one scales, and only the second one survives contact with a CFO.

Cost Explorer still has a job in this lab — as a **cross-check on usage quantities**, not on dollars. `--metrics UsageQuantity` is the reliable field. `--metrics UnblendedCost` will hand you zeros.

## Prerequisites

### 1. Enable Cost Explorer at least 24 hours before you start

Cost Explorer is opt-in, and on first activation AWS takes **up to 24 hours** to prepare historical data. If you enable it the night the lab is due, you will get an empty result and no error explaining why.

```bash
# Enable in the console: Billing and Cost Management > Cost Explorer > Launch
# Then confirm from the CLI (returns data only after preparation completes):
aws ce get-cost-and-usage \
  --time-period Start=2026-11-01,End=2026-12-01 \
  --granularity MONTHLY --metrics UsageQuantity \
  --group-by Type=DIMENSION,Key=SERVICE --region us-east-1
```

Two things can block this call, and they produce different errors:

- `DataUnavailableException` — Cost Explorer is enabled but has not finished preparing. Wait.
- `AccessDeniedException` — your IAM identity cannot read billing data. On some account configurations the **root user** must first activate *IAM user and role access to Billing information* (Account Settings). You cannot fix this from an IAM user, and you cannot fix it in the ten minutes before a deadline.

**If Cost Explorer will not cooperate, the lab is still completable.** Every dollar figure in this lab comes from the rate card. Cost Explorer is a convenience for reading your own usage quantities; you can substitute usage you logged during Labs 2–6. Say in your write-up which source you used.

### 2. The Price List API is your rate card — with one exception

`aws pricing` is free, needs no quota, and is authoritative for everything you deployed:

```bash
aws pricing get-products --service-code AmazonSageMaker --region us-east-1 \
  --filters 'Type=TERM_MATCH,Field=instanceName,Value=ml.m5.large' \
            'Type=TERM_MATCH,Field=regionCode,Value=us-east-1' \
  --query 'PriceList' --output text | python3 -m json.tool | head -40
```

> **The `pricing` endpoint exists only in `us-east-1` and `ap-south-1`.** `--region us-east-1` is not optional, and it does not mean "price things in us-east-1" — that is what the `regionCode` filter is for. Getting this wrong returns an endpoint error, not a price.

**The exception is Bedrock.** The Price List API's Bedrock coverage in `us-east-1` is incomplete: it exposes input-token prices for a handful of older Claude models and **no output-token prices at all**. Verified 2026-08-01. If your second system is Track B or Track C, take LLM token prices from the Bedrock pricing page, cite the date you read it, and state it as an assumption. Do not silently substitute the Price List figure — an input-only cost model understates an LLM system by roughly half.

### 3. Two case numbers do not reconcile. You must handle this explicitly.

This is a real inconsistency in the NorthStar case material, not a trick.

| Source | Figure | Population and window |
|---|---|---|
| Case overview | churn **18% per year** | 2.1M active customers, annual |
| Training dataset | positive rate **22.0%** | ~10,000 sampled customers, 90-day label |

A 22.0% rate per 90 days compounds to roughly **63% per year**, which is not 18%. The two figures describe different populations over different windows, and the sampled dataset is not a random draw from the customer base.

**What this means for your work:**

- **Business math** (value, ROI, lost LTV, the CDO's target) uses the case figures: 2.1M active customers, 18% annual churn, $340 lifetime value — which multiply to the case's stated $128.5M annual churn problem. That headline number is reproducible, and your analysis should reconcile to it.
- **Model math** (recall, precision, lift, achievable coverage) uses the measured dataset figures: 22.0% base rate, Recall@10% of **0.3106** against a ceiling near 0.45.
- **Never multiply one by the other without saying so.** Any place your analysis crosses between them, state the bridging assumption in one sentence. Task 2 is graded partly on whether you did.

### 4. The churn label is 90 days

Lab 2 derives `churn_label` from a **90-day holdout window** following the observation period. Lab 3 trains against it, Lab 6's drift plan depends on it, and the case overview states it. Everything in Lab 7 — measurement windows, attribution windows, time-to-outcome — must use **90 days**.

Watch the distinction between the *label* window and the *feature* windows, because both appear in the same table. `purchase_frequency_30d` looks **back** 30 days to build a feature; `churn_label` looks **forward** 90 days to record an outcome. A value methodology note that reports outcomes on a 30-day cycle has confused the two, and it will cost points in Task 4.

## Your Measured Inputs

You are not starting from a blank page. These are real, from the reference implementation, and you may use them directly. If your own Labs 2–6 produced different numbers, use yours and say so.

**Model performance** — `models/churn/train_reference.py` (the Athena path), measured end to end on 2026-08-02 against the 10,000-customer dataset, model-registry version **v4**, deterministic `ORDER BY` pull, `seed=42`, `test_size=0.30`. These supersede every earlier figure in circulation. Note the lift is *smaller* than previously published: the recency-only baseline is much stronger at this scale, so feature engineering buys less than the course used to claim — but for the first time the margin has an interval around it that excludes zero.

| Quantity | Value |
|---|---|
| AUC-ROC | **0.7696** |
| Recency-only baseline AUC | 0.7233 |
| AUC lift over baseline | **+0.0464** |
| Lift 95% CI | **[0.0254, 0.0670]** — excludes zero |
| Precision@10% | **0.6833** |
| Recall@10% | **0.3106** |
| Recall@10% theoretical ceiling at 22.0% base rate | **~0.45** |
| Train / test split | 6,999 / 3,000 |
| Lab 4 promotion gate / Lab 6 SLO | Recall@10% ≥ 0.25 |
| Inference latency p95 | **~4.1 ms** |
| Cold-start latency, first call after deploy | ~24 ms |

**Rate card (AWS Price List API, us-east-1, verified 2026-08-01)**

| Item | Rate |
|---|---|
| SageMaker Hosting `ml.t2.medium` | $0.056 / hr |
| SageMaker Hosting `ml.m5.large` | $0.115 / hr |
| SageMaker Hosting `ml.m6g.large` | $0.0924 / hr |
| SageMaker Processing `ml.t3.medium` | $0.05 / hr |
| SageMaker Processing `ml.t3.large` | $0.10 / hr |
| SageMaker Serverless Inference, 2 GB | $0.00004 / sec |
| Glue ETL and Crawler | $0.44 / DPU-hr |
| Glue Flex ETL | $0.29 / DPU-hr |
| Feature Store writes | $1.25 / million request units |
| Feature Store reads | $0.25 / million request units |
| Feature Store online storage | $0.45 / GB-month |
| S3 standard storage | $0.023 / GB-month |
| S3 requests | $0.005 / 1,000 PUT · $0.0004 / 1,000 GET |
| CloudWatch alarm | $0.10 / alarm-month |
| CloudWatch custom metric | $0.30 / metric-month (first 10,000) |
| CloudWatch API request | $0.01 / 1,000 |

> **The Price List API returns one pricing tier, and it may not be yours.** Query `CW:MetricMonitorUsage` and it returns **$0.02** — the rate for accounts publishing over one million metrics. You are publishing about ten, so your rate is **$0.30**. The API answered a question you did not ask. Read the `description` field on every price dimension before you use the number in it. This has produced a 15x error in a real cost model.

**Measured usage, full Labs 1–6 build (reference account, July 2026)**

Reproduced from the table above: hosting 0.5889 / 0.4328 / 0.0192 hr, processing 0.0958 / 0.2283 hr, Glue 1.0311 ETL + 0.4786 crawler DPU-hr, Feature Store 7,967 write RU, S3 764 PUT / 3,260 GET, NAT 4 hr, CodeBuild 10 build-min.

> **These are July 2026 *cumulative* usage figures from Cost Explorer, measured on the retired 1,200-customer dataset.** Two cautions. First, they are a month's total across every run, **not the cost of one pass** — scaling them as though they were per-run is a real error, and this course's own cost model made it until 2026-08-03. Second, the dataset is now 8x larger: a single measured ETL pass is roughly **380–500 DPU-seconds** across the two Glue jobs.
>
> **That range is the point, not a hedge.** Four measured single-pass runs on byte-identical data gave **430, 400, 380 and 502** total DPU-seconds — a **32% spread** with no change to the input, the code, or the configuration. Glue bills on DPU-hours it decides you consumed, and that number moves run to run.
>
> So: **do not report a single measured DPU figure as though it were a constant, and do not treat a number outside someone else's measurement as an error.** If your pass lands at 380 or at 500, both are normal. If your cost model's conclusion changes materially between those two ends, the model is too sensitive to a noisy input and you should say so — that observation is worth more marks than a precise-looking point estimate. Use *your own* measured usage, state the range you observed, and say which quantity you are scaling.

Two of these are worth noticing before you use them. The `ml.t3.large` figure of 0.0958 hr is **5 min 45 s** — one successful monitoring analyzer run. The `ml.t3.medium` figure of 0.2283 hr is **13 min 42 s** — one analyzer run that ran out of memory and failed. **Failed jobs bill.** A cost model built only from successful runs understates the truth, and in early-stage ML the failures are frequently the larger number. Yours will be.

> **These two figures are from SageMaker Model Monitor, which Lab 6 no longer uses** — its Spark analyzer needed `ml.t3.large` and OOM'd on `ml.t3.medium`. Lab 6 now runs Evidently, which completes the same comparison in **1 min 59 s on `ml.t3.medium`** for about **$0.0017**. The July figures are left here deliberately, because the comparison is the lesson: **a tool substitution changed this line item by roughly 9x while changing nothing about the business question being answered.** When you build your cost model in Task 2, that is the kind of lever worth looking for — far more of your bill is architecture choice than volume.

> **The same lever, one order of magnitude larger — experiment tracking.** AWS offers two MLflow products that do the same job for your training runs:
>
> | | MLflow **App** (what Lab 3 uses) | MLflow **Tracking Server** |
> |---|---|---|
> | Billing model | serverless, **no additional charge** | **$0.60/hr**, from creation to deletion |
> | Cost per month, left running | **$0.00** | **~$438** |
> | Cost while you sleep | $0.00 | $4.80/night |
>
> **Model this one in Task 2 and notice what it does to your unit economics.** The tracking server is not a bigger instance or a faster tier — it is the *same capability with a different billing model*, and it costs infinitely more than free. A platform team that picked it without asking would have added ~$5,300/year per environment to NorthStar's bill for nothing.
>
> This is the shape of most real AI cost overruns. They are rarely "we used too much"; they are usually "we provisioned something that bills by the hour to do a job that bills by the request." **When you present your scorecard, an architecture line item you eliminated is worth more than a usage line item you trimmed** — and it is far more defensible to a CFO, because it does not require anyone to do less work.

## Deliverable

**One file: `docs/lab7-value-scorecard.md`**, with five top-level sections numbered to match the tasks:

```
## 1. Metric Pyramid
## 2. Unit Economics
## 3. Executive Value Scorecard
## 4. Value Methodology Note
## 5. Measurement Reflection
```

**Plus one machine-checkable artifact: `docs/lab7-cost-model.csv`**, with the header

```csv
line_item,category,usage_quantity,unit,rate_usd,monthly_cost_usd,source,assumption
```

Every dollar figure that appears in Section 2 must appear as a row in this file, and the rows must sum to your stated total. This is graded. It exists because a cost model whose arithmetic cannot be checked is an opinion.

---

## Tasks

### Task 1 — Metric Pyramid (25 points)

Build the four-layer metric pyramid for **two** NorthStar AI systems:

1. **Churn prediction** (required — you deployed it), and
2. **One of** offer generation (Track B) or the customer service agent (Track C).

> **You do not need to have deployed the second system.** Bedrock inference quotas start at zero on a new account and Track B/C may have been unavailable to you. Task 1 is a design and measurement-architecture exercise; the second pyramid is graded on the quality of its reasoning against the case material, not on whether the system exists in your account. Say in one line which track you chose and whether you deployed it.

**The four layers:**

| Layer | Description | Example (Churn) |
|-------|-------------|-----------------|
| Model / System | Technical performance | AUC-ROC 0.7696, p95 latency 4.1 ms |
| Model Output | What the model emits | Score distribution, daily alert volume |
| User Experience | How people interact with the output | Offer acceptance rate, campaign click-through |
| Business Outcome | Revenue or cost impact | 90-day retention rate, prevented churn revenue |

**Required for each system:**

- At least **2 metrics per layer** (8 per system minimum).
- For each metric: **calculation method, owner, update frequency, and the decision it informs.** An owner is a named role from the NorthStar stakeholder table, not "the team." A decision is a stated threshold and the action taken when it is crossed.
- **Causal link analysis.** For every adjacent-layer link in the chain, label it **Validated** or **Assumed**. A link is *Validated* only if both metrics are measured on the same population over the same window by an existing pipeline. Everything else is *Assumed*. For each Assumed link, name the experiment that would validate it.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Pyramid complete for both systems | 10 | Each system has ≥8 metrics correctly placed across all 4 layers |
| Each metric has all four attributes | 8 | Calculation, owner (named role), frequency, and decision threshold present for every metric |
| Causal links classified, assumptions surfaced | 7 | Every adjacent link labeled; ≥2 links per system labeled Assumed with a stated validating experiment |

### Task 2 — Unit Economics (25 points)

All four parts. Every figure traces to `docs/lab7-cost-model.csv`.

**2a. Pull the rate card (5 points)**

Use `aws pricing get-products` to retrieve the current published rate for **at least four** resources your platform actually uses. Show the command and the returned price dimension for each, including the `description` field.

State the date you pulled it. AWS prices change; a rate card without a date is not a rate card.

**2b. Cost per 1,000 predictions — churn model (8 points)**

Compute the fully-loaded cost per prediction for the churn model **at NorthStar production scale**: 2.1M active customers scored weekly.

Four components, all required:

- **Inference compute** — as architected in Labs 5–6, i.e. a persistent real-time endpoint
- **Amortized training** — training cost ÷ predictions served over the model's lifetime
- **Feature Store online reads** — one read per prediction
- **Data pipeline allocated to churn** — Glue ETL and crawler cost, divided across the models the pipeline serves

Present the result as **`$X.XXX per 1,000 predictions`** and show the arithmetic.

> The measured Glue DPU-hours in your inputs come from a 19,500-row lab dataset. NorthStar is not that size. **Derive your scale factor from the case** — annual revenue and average order value give you transaction volume — and state it. A cost model that silently applies lab-scale pipeline cost to a 2.1M-customer business is off by more than an order of magnitude.

> One component may legitimately come out at or near zero. If it does, **say why in one sentence.** The reference implementation trains locally rather than on SageMaker, which does not make training free — it moves the cost into a category that does not appear on any AWS bill. Naming a cost you moved rather than eliminated is the point of the exercise.

**2c. Total platform cost (7 points)**

Estimate the monthly cost of the full NorthStar platform — all three AI systems — across six categories:

| Category | Monthly Cost ($) | Stated Assumption |
|----------|-----------------|-------------------|
| Compute (training) | | |
| Compute (inference) | | |
| Data pipeline, storage and transfer | | |
| Third-party APIs and services (Bedrock) | | |
| Human labor (estimate at $80/hr) | | |
| Platform and tooling | | |
| **Total** | | |

> Pipeline compute (Glue) belongs in **row 3**, not in either compute row. The six-category taxonomy from the chapter splits compute by *model* lifecycle stage and treats the data platform as one line. Put it wherever you like, but put it somewhere, exactly once, and say where.

Compare your total against NorthStar's stated **$85,000/month** AI platform budget. If your total is a small fraction of the budget, that is a finding, not an error — report it and say what it implies about which decisions actually matter.

**2d. One cost optimization (5 points)**

Identify **one specific** optimization, quantify it, and state the tradeoff you accept.

Quantified means: the current cost, the optimized cost, the dollar and percentage saving, and the arithmetic connecting them.

The tradeoff must be **operational, not rhetorical.** "Slightly less flexible" is not a tradeoff. If your optimization changes the serving architecture, check it against the four SLOs you wrote in Lab 6 and say which of them survive it. Some optimizations on this platform invalidate an SLO you already committed to; finding that out here is much cheaper than finding it out in production.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Rate card pulled from the API with dates | 5 | ≥4 resources, command shown, `description` field reproduced, date stated |
| Cost per 1,000 predictions, all 4 components | 8 | Arithmetic shown; scale factor for the pipeline derived and stated; any zero component explained |
| Six-category platform cost with assumptions | 7 | Every row has a figure and a stated assumption; total compared to the $85K budget; `lab7-cost-model.csv` present and sums to the stated total |
| Optimization specific, quantified, tradeoff real | 5 | Names a specific AWS feature or architecture change; before/after arithmetic; tradeoff checked against Lab 6 SLOs |

### Task 3 — Executive Value Scorecard (25 points)

Produce a one-page scorecard in Section 3. Audience: **Maya Chen (CDO) and Robert Hess (CFO).** No ML metrics. No AUC, no PSI, no recall. Write for a business reader who controls the budget.

**Required structure:**

```markdown
## NorthStar AI Platform — Q4 2026 Value Scorecard

### Platform Summary
[2-3 sentences: what the platform does and why it was built]

### Systems in Production
| System | Business Metric | Current Performance | vs. Target | Status |
|--------|----------------|---------------------|------------|--------|
| Churn Prediction | | | | On Track / Watch / Action Required |
| [Second system] | | | | |

### Can We Hit the Stated Target?
[Required. See below.]

### Attribution
[How would business impact be measured? What is the counterfactual?
What is your confidence level and why?]

### Investment Recommendation
| System | Recommendation | Rationale |
|--------|----------------|-----------|
| Churn Prediction | Expand / Hold / Redesign / Decommission | |
| [Second system] | | |

### Open Questions
[What measurement gaps remain? What experiments would close them?]
```

**The "Can We Hit the Stated Target?" section is the heart of this task.**

The CDO's stated success metric for churn prediction is: **reduce the annual churn rate from 18% to 14% within one year of deployment.** The retention program contacts only the **top 10% highest-risk customers**.

Work out what that target actually requires, given the model you measured:

- How many customers must be retained per year to move the rate by 4 percentage points?
- How many at-risk customers does the model actually place in the contactable top decile, at its measured Recall@10%?
- Therefore, what fraction of contacted customers must the retention offer save?
- Is that fraction achievable? Compare it to a stated, sourced benchmark for retention-offer effectiveness.
- If it is not achievable, what *is* achievable — and what would have to change (model recall, decile coverage, offer conversion) to close the gap?

Then tell the CDO, in the scorecard, in plain language. **A scorecard that reports the target as "on track" without doing this arithmetic has failed the task**, regardless of how well written it is.

You are not being asked to condemn the platform. A system can be a strong investment and still miss a target that was set before anyone measured the model. Reporting both, clearly, is the job.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Target feasibility computed and reported honestly | 10 | Required save rate derived from measured recall and shown; compared to a sourced benchmark; verdict stated plainly; achievable alternative quantified if the target is not reachable |
| Readable by a non-technical executive | 8 | No ML term appears without plain-language translation; no AUC, PSI, recall, or drift vocabulary in Section 3 |
| Attribution method explicitly stated | 7 | Names the specific method (randomized holdout, A/B test, difference-in-differences), states the counterfactual, states confidence level with a reason |

### Task 4 — Value Methodology Note (15 points)

Write a complete value methodology note for **one** NorthStar AI system, in Section 4. **All 13 fields.** No blanks, no "TBD."

```markdown
## Value Methodology Note: [System Name]

| Field | Value |
|-------|-------|
| 1. System name | |
| 2. Business objective | |
| 3. Value dimension (efficiency / revenue / risk / experience) | |
| 4. Primary metric | |
| 5. Guardrail metrics (>=2) | |
| 6. Attribution method | |
| 7. Counterfactual | |
| 8. Measurement window | |
| 9. Time to observe outcome | |
| 10. Confidence level (Low / Medium / High) | |
| 11. Known confounders | |
| 12. Financial conversion logic | |
| 13. Metric owner and review cadence | |
```

Two fields carry most of the weight:

- **Counterfactual (7)** must describe what happens *without* the AI system in operational terms. "Nothing" and "no AI" are not counterfactuals. "The retention team manually segments on days-since-last-purchase greater than 60, which surfaces roughly X% of the churners the model finds" is one.
- **Time to observe outcome (9)** is **90 days**, because that is the label. If your measurement window in field 8 is shorter than field 9, your methodology reports results before the outcome exists. Say how you handle the gap.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 13 fields completed substantively | 10 | No field blank, "TBD," or a restatement of its own label |
| Counterfactual and outcome timing are specific and consistent | 5 | Counterfactual describes concrete current-state behavior; measurement window is reconciled against the 90-day label |

### Task 5 — Measurement Reflection (10 points)

Roughly 300 words in Section 5.

1. What are the **two weakest measurement assumptions** in your metric pyramid? Name the specific causal link, not "the model might be wrong."
2. For each: what experiment validates or invalidates it? State what you measure, the population, the duration, and the success criterion. A sample-size or power sketch earns full credit; an experiment with no n is an idea, not a design.
3. Which pyramid layer is **least observed** in the platform as built? What specific data is missing, what engineering would capture it, and how long would that take?

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Two weak assumptions named precisely | 5 | Each is a specific causal link between two named metrics, and is falsifiable |
| Experiments are actionable | 5 | Each states metric, population, duration, and success criterion |

---

## Traps Already Mapped — do not rediscover

1. **Cost Explorer will report $0.00 for a month in which you ran the entire platform.** Free tier absorbs it. Use `--metrics UsageQuantity`, never `UnblendedCost`, and build dollars from the rate card.
2. **Cost Explorer takes up to 24 hours to prepare data after first activation.** Enable it the day before, not the hour before.
3. **An IAM user may be denied billing data** until the root user activates IAM access to billing. You cannot fix this from the IAM user, and it is not a permissions policy you can attach.
4. **The `pricing` API endpoint exists only in `us-east-1` and `ap-south-1`.** `--region` selects the endpoint; the `regionCode` filter selects what you are pricing. They are different things.
5. **The Price List API returns one pricing tier and does not tell you it is the wrong one.** `CW:MetricMonitorUsage` returns $0.02 (the over-1M-metrics tier) when your actual rate is $0.30. Always read the `description` field.
6. **Bedrock output-token prices are absent from the Price List API** in us-east-1, and its Claude model coverage is stale. Use the pricing page and cite the date.
7. **Failed jobs bill.** The reference account spent more instance time on one analyzer run that ran out of memory (13 min 42 s) than on the one that succeeded (5 min 45 s). Cost models built from successful runs are optimistic by construction.
8. **The 18%/year case figure and the 22.0% dataset figure are not the same quantity.** Different population, different window. Mixing them produces confident nonsense.
9. **The churn label looks forward 90 days; several features look back 30.** They sit in the same feature table and are easy to conflate. Any measurement window shorter than 90 days reports outcomes that have not happened yet.
10. **`ModelLatency` is in microseconds** (carried from Lab 6). If you cite latency in a cost or SLO context, cite the unit.
11. **A real-time endpoint bills 24×7 for a weekly batch workload.** Both Lab 5 and Lab 6 built one, deliberately, because they were teaching deployment and monitoring. Whether that is the right architecture for *this* workload is a Task 2d question, and it has a large answer.
12. **Recall@10% is capped near 0.45** by the base rate and the decile constraint — you cannot retrieve more churners than fit in the 10% of the population you are allowed to contact. Any business projection implying recall above that ceiling is arithmetically impossible, not merely optimistic.

## Teardown

**Lab 7 creates nothing.** But it is the last lab, and the teardown gate from Labs 2–6 still applies to everything you built earlier.

Before you submit, run the all-region sweep one final time and confirm the account is clean:

```bash
bash scripts/teardown-lab6.sh    # idempotent; safe to run when nothing is left
```

Then confirm independently, in every region you have ever touched, that there are no:

- SageMaker endpoints, endpoint configs, or models
- Monitoring schedules or in-flight processing jobs
- Application Auto Scaling scalable targets
- CloudWatch anomaly detectors *(these survive `terraform destroy` — check for them explicitly)*
- NAT gateways or unattached Elastic IPs

**An endpoint still running after the semester deadline is a 10-point deduction on this lab**, on top of whatever it costs you. Custom CloudWatch metrics cannot be deleted and expire after 15 months of no data; that is expected and already accounted for.

## Final Notes

**The platform you built across these seven labs covers:**

- Infrastructure as Code on AWS (Lab 1)
- Production data pipelines and a feature store (Lab 2)
- Three AI system types: traditional ML, RAG/LLM, and agentic (Lab 3)
- Automated model lifecycle with CI/CD and testing (Lab 4)
- Production deployment with canary rollout, rollback, and security documentation (Lab 5)
- Five-layer monitoring, SLOs, error budgets, and incident runbooks (Lab 6)
- Economic analysis and business value measurement (Lab 7)

If you take one thing from Lab 7, take this: **the cost side of an AI business case can be computed to three decimal places, and the value side usually rests on a single parameter nobody has measured.** In this platform, the entire ROI turns on the retention offer's save rate — a number that appears in no dashboard, no model card, and no AWS bill. The engineering discipline that matters most at this level is knowing which of your numbers are measured and which are assumed, and never letting the second kind be mistaken for the first.

**The team project** extends this platform with AI governance, closing-the-loop feedback mechanisms, and a new AI system of your team's choosing. Use the NorthStar platform as your architecture reference.

**Academic integrity:** You may discuss lab approaches with classmates, but the code, documentation, and analysis you submit must be your own. Submitting another student's code, even partially, is a violation of the BYU Honor Code.
