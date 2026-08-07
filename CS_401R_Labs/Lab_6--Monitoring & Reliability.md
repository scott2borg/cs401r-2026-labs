# Lab 6: Monitoring & Reliability

**Assigned:** Thu Nov 12 | **Due:** Sat Nov 28, midnight
**Chapters:** *Metrics, Benchmarks & Guardrails*, *Monitoring & Observability*, *Reliability Engineering*
**Builds on:** Labs 1–5 — instruments the production system deployed in Lab 5

## Objective

A deployed model with no monitoring is a liability. This lab instruments the NorthStar platform end-to-end: five monitoring layers, a full alert architecture, SLOs with error budgets, and operational runbooks for failure scenarios. After this lab, your platform can fail gracefully and recover fast.

## Starter Kit

**None.** Labs 5–7 have no starter kit. Lab 6 instruments what Lab 5 deployed, using the IAM roles created in Lab 2 and the endpoint created in Lab 5.

## Read This First — Cost

**Lab 6 is the most expensive lab in this course.** Not because any one resource is costly, but because it is the only lab that asks you to leave an hourly-billing resource running while you wait for something to happen.

Lab 5 taught you that a SageMaker endpoint bills from `InService` until deletion. Lab 6 re-creates that endpoint *and* adds a second billing source:

| Resource                    | Rate                 | Notes                                                    |
| --------------------------- | -------------------- | -------------------------------------------------------- |
| Endpoint — `ml.t2.medium`   | **$0.056 / hr**      | Where Lab 5 starts you                                   |
| Endpoint — `ml.m5.large`    | **$0.115 / hr**      | Only if your Lab 5 quota increase came through           |
| Evidently processing job    | **$0.05 / hr**       | `ml.t3.medium`, billed per second, only while a job runs |
| CloudWatch alarm            | $0.10 / alarm-month  | Prorated hourly; 6 alerts ≈ $0.60/mo if left             |
| CloudWatch custom metric    | $0.30 / metric-month | **Not prorated** — you pay for the month                 |
| CloudWatch dashboard        | free (first 3)       | Then $3/mo                                               |

The drift job is the cheapest thing in this lab. **Measured 2026-08-07 on `ml.t3.medium`: 10,000 baseline rows against 800 captured records ran in 1 min 59 s of billed instance time and cost about $0.0017.** Round it to a fifth of a cent per run. Run it ten times while you get the inputs right and you have spent two cents.

Your bill in this lab is essentially the endpoint, and only the endpoint.

What this actually costs you — the column that applies depends on which instance Lab 5 left you on:

| If you… | On `ml.t2.medium` | On `ml.m5.large` |
|---|---|---|
| Work in one focused session and tear down (3 h) | **$0.49** | **$0.67** |
| Leave it running overnight (14 h) | **$1.13** | **$1.95** |
| Forget for three days (72 h) | **$4.47** | **$8.72** |
| Forget for a week (168 h) | **$10.01** | **$19.93** |

Burn rate with the endpoint live and one drift run per hour: **$0.0577/hr** on `t2.medium`, **$0.1167/hr** on `m5.large`.

> **A single forgotten Lab 6 endpoint breaches the entire course account's $10/month budget alarm in 168 hours (7 days) on `t2.medium`, or 83 hours (3.5 days) on `m5.large`.** You have a 16-day submission window, so either number is reachable by simply forgetting. Do the lab in one sitting and tear it down.

**Read that table for what it is actually telling you.** Every meaningful number in it is the endpoint. The monitoring — the entire subject of this lab — rounds to nothing. That is the normal shape of production ML economics: *serving* is the recurring cost, and *observability* is close to free by comparison. The instinct to skip monitoring to save money is backwards, and this bill is the proof.

If you automate the analysis on a timer (EventBridge, a cron job, a loop), **that timer keeps launching billable jobs whether or not you are still working, and whether or not the endpoint still exists.** `scripts/teardown-lab5.sh` knows nothing about monitoring. **Use `scripts/teardown-lab6.sh`** — it stops in-flight processing jobs before deleting the endpoint.

## Why this lab uses Evidently and not SageMaker Model Monitor

SageMaker Model Monitor is the obvious tool for this lab, and you cannot use it. **Monitoring schedules are closed to new AWS accounts:**

```
ValidationException: This operation is in maintenance mode and is not
available to new customers. Existing customers are unaffected.
```

Both `CreateMonitoringSchedule` and `CreateDataQualityJobDefinition` return this. It is not a quota, not a permission, and not something you did wrong — AWS closed the API to accounts that were not already using it. **Every account in this course is new.** No permission fixes it and there is nothing to request.

So this lab uses **[Evidently](https://github.com/evidentlyai/evidently)**, an open-source Python library for drift detection, running inside a SageMaker Processing Job. You keep the managed compute; you drop the managed control plane that was closed to you.

> **Do not confuse this with Amazon CloudWatch Evidently.** That was an unrelated AWS service for feature flags and A/B experiments, it never did model monitoring, and AWS ended support for it on **16 October 2025**. If you find AWS documentation for "Evidently", it is almost certainly about the dead feature-flag service. The library you want is `pip install evidently` and its docs are at `docs.evidentlyai.com`.

This substitution is worth more than it costs. A managed schedule is a checkbox that hides the analysis behind it. Running Evidently yourself means you must decide *what test to run on which feature at what threshold* — which is exactly what Task 2 asks you to justify, and exactly the judgement the checkbox was making silently on your behalf.

There is also a practical dividend: Model Monitor's analyzer is a Spark container that needs 8 GB. Evidently is pandas. It runs comfortably on the cheapest instance you have quota for.

## Prerequisites — do this before Task 1

Run the pre-flight check:

```bash
bash scripts/preflight-lab6.sh
```

### 0. Use `ml.t3.medium` — and understand why you have no other choice

**Your AWS account's processing-job quota is 0 for every non-burstable instance type.** Not low — zero. `ml.m5.large`, `ml.c5.*`, `ml.m4.*`, `ml.r5.*` and every other general-purpose family will reject the job immediately:

```
ResourceLimitExceeded: The account-level service limit
'ml.m5.large for processing job usage' is 0 Instances
```

Of the 126 processing instance types, exactly **three** have a non-zero AWS default, and all three are burstable: `ml.t3.medium` (4), `ml.t3.large` (4), `ml.t3.xlarge` (2). Verified against `get-aws-default-service-quota` on 2026-07-31.

Check your own before you start:

```bash
aws service-quotas get-service-quota --service-code sagemaker \
  --quota-code L-0CE343FE --query 'Quota.Value' --output text   # ml.t3.medium processing
```

**`ml.t3.medium` (4 GB) is enough.** Verified 2026-08-07: a 10,000-row baseline against 800 captured records completed in **1 min 59 s** of billed time. You do not need `ml.t3.large` and you must not file a quota increase for this lab.

> **This is where the tool choice pays for itself.** The same comparison under Model Monitor's Spark analyzer **fails** on `ml.t3.medium` — it exhausts 4 GB, takes **13 min 43 s** to do it, and then blames your data instead of the instance: *"Please use an instance type with more memory, or reduce the size of job data processed on an instance."* That message sends you off shrinking a dataset that was never the problem. Evidently on the same instance and the same data finishes in under two minutes.
>
> **Note the inversion from Lab 5.** Lab 5's trap was that *burstable instances cannot be auto-scaling targets* — you were forced off `ml.t3.*` onto `ml.m5.large`. In Lab 6 the constraint runs exactly the other way: burstable is the only class with any default processing quota at all. Same instance family, opposite conclusion, one lab apart.
>
> **Endpoint quota, training quota, and processing quota are three completely separate numbers**, and having one tells you nothing about the others. `ml.m5.large` has a *different* quota for each. The AWS default for all three on-demand families is 0. An endpoint that deployed fine in Lab 5 tells you nothing about whether a processing job will run in Lab 6.

### 1. Your endpoint must have data capture enabled

Evidently analyzes inference data that the endpoint captured to S3. **No capture means nothing to analyze.** The launcher checks the capture prefix before it starts a billable job and refuses to launch against an empty one — but understand what it is protecting you from.

**Endpoint configs are immutable.** Capture cannot be switched on for a running endpoint. If your endpoint was deployed without it, you must create a new endpoint config and call `update-endpoint` (~3 min 47 s, zero downtime):

```bash
python deployment/configs/canary_deploy_realtime.py \
  --model-package-arn <arn> --role-arn <arn>
```

Capture lands under `s3://<bucket>/datacapture/<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/`. It is written **asynchronously** and lags several minutes behind your first invocation. Baselining against an empty prefix fails with a confusing schema error, not a helpful "no input" error — so invoke the endpoint, wait, and confirm objects exist before you baseline.

### 2. Use the ModelMonitorExecution role, not the ModelMonitor role

The platform has two similarly named roles, and they are **not interchangeable**:

| Role | What it is | Use for                                       |
|---|---|---|
| `northstar-dev-ModelMonitor` | **Observer** identity. Read-only by design: no S3 write, no ECR pull. | Humans and automation that watch the platform |
| `northstar-dev-ModelMonitorExecution` | **Service execution** identity. Writes reports, pulls the container. | **The Evidently processing job — this lab**   |

The drift job is a batch job whose entire purpose is to *write* its findings (`drift_report.json`, `drift_violations.json`) and it cannot start without pulling its container from ECR. Hand it the observer role and the job fails several minutes in as an opaque `ProcessingJobStatus: Failed`.

This distinction — an identity that observes versus an identity that executes — is the design point, not a technicality. Note it in your Task 3 deliverable.

## Tasks

### Task 1 — Five-Layer Monitoring Implementation (35 points)

Implement monitoring across all five layers for the NorthStar churn model. All layers must surface in a single **CloudWatch Dashboard** named `NorthStar-AI-Platform`.

| Layer | What to Monitor | Tool                                           | Threshold |
| ------------------ | ---------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------- |
| **Infrastructure** | SageMaker endpoint CPU, memory | CloudWatch Metrics                             | CPU > 80% → alert |
| **Pipeline** | Glue job success/failure rate | CloudWatch Events                              | Any failure → P2 alert |
| **Model** | Data drift (PSI on top 3 features) | Evidently, run as a processing job             | PSI > 0.2 → alert (metric published by you) |
| **Application** | Inference latency p50, p95, p99 | CloudWatch Metrics                             | p95 > 200 ms → alert (`ModelLatency` threshold `200000` — see note) |
| **Business** | Daily churn alert volume (proxy) | CloudWatch Custom Metric                       | Volume drop >30% vs. 7-day avg → alert |

> **`ModelLatency` is emitted in MICROSECONDS.** Every latency threshold in this lab is written in milliseconds because that is how humans and SLAs talk, but CloudWatch does not. 200 ms is `200000`; 500 ms is `500000`. Writing `200` builds an alarm that trips at 0.2 ms — well below a healthy endpoint's normal latency, measured at roughly **4,100 µs (4.1 ms)** on `ml.m5.large` in Lab 5. That alarm sits in `ALARM` permanently and any automation wired to it fires against a healthy system. Verified on AWS 2026-07-30. Check the `Unit` field in `get-metric-statistics` output before setting any threshold.
>
> Related: the **first invocation after a deploy runs ~6x slower** (~24,000 µs measured) as the container warms. An alarm with `EvaluationPeriods: 1` will trip on your own deployment.
>
**Requirements:**
- A **baseline** exported from your Lab 2 training feature set — a CSV of the **11 features the endpoint receives** — uploaded to `s3://<bucket>/monitoring/baseline/`.
- A **drift analysis run** — Evidently executed as a processing job against your captured inference data, producing `drift_report.json` and `drift_violations.json`. Commit both.
- At least one custom CloudWatch metric pushed programmatically (business layer)
- Dashboard JSON exported and committed to `monitoring/dashboards/northstar-dashboard.json`

**Running the drift analysis.** The launcher uploads the analysis script, checks that captured data actually exists, and submits the processing job:

```bash
python monitoring/run_evidently_job.py \
  --bucket northstar-dev-data-<account> \
  --role-arn arn:aws:iam::<account>:role/northstar-dev-ModelMonitorExecution \
  --endpoint northstar-churn-prod \
  --variant champion
```

The job runs the stock SageMaker scikit-learn container and `pip install`s Evidently at start-up. Two details in that command are load-bearing:

```
683313688378.dkr.ecr.us-east-1.amazonaws.com/sagemaker-scikit-learn:1.4-2-py312-cpu-py3
pip install evidently==0.7.21
```

> **The `py312` tag is required.** Evidently needs **Python ≥ 3.10**. The older `sklearn 1.2-1` processing image ships an earlier Python and the install fails. If you copy an image URI from an older tutorial, this is what breaks.
>
> **Pin the version.** Evidently's API broke at 0.7 — `column_mapping` was replaced by `DataDefinition`, and you can no longer hand a Report a bare DataFrame; it must be wrapped in a `Dataset`. Most tutorials online predate this and fail with an `ImportError`. An unpinned install also means your lab breaks the day upstream ships 0.8.
>
> **You do not need a NAT gateway for the `pip install`.** A processing job launched without a VPC config has egress through SageMaker's managed network. Verified 2026-08-07.

**Expect alarming-looking pip output that is not an error.** Installing Evidently upgrades `protobuf` and `urllib3` past the versions the sklearn container pins, and pip says so loudly:

```
ERROR: pip's dependency resolver does not currently take into account all the
packages that are installed. This behaviour is the source of the following
dependency conflicts.
sagemaker-sklearn-container 2.0 requires protobuf==3.20.2, but you have protobuf 7.35.1
```

**The job succeeds anyway** — nothing in the drift analysis uses those packages. Verified. But note the consequence: `botocore` inside that container is now on an unsupported `urllib3`, so **do not try to call `put-metric-data` from inside the job.** Publish your metric from the launcher after the job returns, which is what `publish_metrics.py` does.

**Capture is partitioned per variant** — `datacapture/<endpoint>/<variant>/<yyyy>/<mm>/<dd>/<hh>/`. If you ran a two-variant canary in Lab 5, point the job at one variant's prefix, and say in your write-up which one and why.

Reference run, verified 2026-08-07 on `ml.t3.medium`: 10,000 baseline rows against 800 captured records, **1 min 59 s** billed. Output:

```
feature                      test         value   thresh  drift
days_since_last_purchase     psi         0.0227      0.2    no
purchase_frequency_30d       psi         6.8354      0.2   YES
avg_order_value              psi         1.3880      0.2   YES
category_diversity_score     ks          0.8945     0.05    no
total_spend_90d              ks          0.7629     0.05    no
```

Your numbers will differ; the *shape* of the output should not.

> **The one thing most likely to make your results silently wrong.**
>
> **Evidently returns a different kind of number depending on the test.** PSI returns a **distance statistic** — it *rises* with drift, so drift means `value > threshold`. KS returns a **p-value** — it *falls* with drift, so drift means `value < threshold`. Measured on synthetic data as the mean shift increases:
>
> | mean shift | `ks` (p-value) | `psi` (statistic) |
> |---|---|---|
> | 0 | 0.272552 | 0.0235 |
> | 2 | 0.000000 | 0.0472 |
> | 5 | 0.000000 | 0.2757 |
> | 15 | 0.000000 | 2.3176 |
>
> They move in **opposite directions.** If you loop over mixed tests with one `if value > threshold`, KS is inverted and reports **no drift on maximally drifted data**, because `0.0` is not greater than `0.05`. Nothing errors. Your report looks clean. This is the single most dangerous defect available in this lab, and it is a reasoning error, not an infrastructure one — no amount of AWS debugging will find it.
>
> **Two more that will cost you a run:**
>
> **1. Baseline the 11 features the *endpoint* receives** — not the full training frame. `churn_label` is the target and `churn_risk_score` is the Lab 3 recency baseline; neither is a model input. A baseline over 12 or 13 columns produces schema noise that never names its real cause.
>
> **2. Do not invoke with batched rows if you intend to monitor the traffic.** Send more than one CSV row per request and the whole payload is captured as a single string, so 200 batched predictions become one row in your comparison window. Score one row per request.
>
> **3. Use at least ~500 predictions in the comparison window.** A small window manufactures drift that is not there. The analysis script warns you when the window is under 500 rather than letting you believe a false positive.

**Rubric:**

| Item                                         | Points | Pass Criteria |
|------|--------|---------------|
| All 5 layers visible in CloudWatch Dashboard | 15 | TA can open the dashboard and see at least one metric per layer |
| Evidently baseline **and** drift analysis run | 10 | A committed baseline CSV over the 11 endpoint features, **and** `drift_report.json` + `drift_violations.json` from an Evidently processing job over captured data. A Model Monitor schedule is NOT required and cannot be created — see the note above. |
| Custom metric pushed for business layer      | 5 | `aws cloudwatch get-metric-statistics` returns data for the custom metric |
| Dashboard JSON committed                     | 5 | `monitoring/dashboards/northstar-dashboard.json` is valid CloudWatch Dashboard JSON |

> **Grading standard carried forward from Lab 5:** prefer *observed* evidence over configuration screenshots. A `drift_violations.json` with real numbers in it beats a console screenshot of a job that has never executed.

### Task 2 — Drift Detection Plan (15 points)

Write a drift detection plan for the NorthStar churn model in `docs/lab6-runbook.md`.

**Required content:**
1. **Drift types most likely for this domain**: Which of (data drift, concept drift, model degradation) are most likely for customer churn prediction in retail? Justify with reference to NorthStar's business context (seasonal promotions, catalog changes, economic shifts).
2. **Statistical tests chosen**: For each feature you monitor, specify the test (PSI, KS, or JSD), the baseline window, and the threshold.
3. **Concept drift detection**: The churn label is only observable after the full 90-day holdout window has elapsed, so ground truth for a prediction made today does not exist until three months from now. How will you detect concept drift in the meantime? Propose a proxy signal and state its lag.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Drift type analysis references NorthStar specifics | 5 | Mentions at least one NorthStar-specific driver (e.g., holiday promotions, catalog refresh) |
| Statistical test specified per feature with threshold | 5 | At least 3 features have named tests and numeric thresholds |
| Concept drift proxy proposed and reasoned | 5 | Proposes a specific observable signal (e.g., model score distribution shift, early return rate) |

### Task 3 — Alert Architecture (15 points)

Define the full alert set for the NorthStar churn model and offer generation system in `monitoring/alerts/`.

**Required deliverable:** An alert specification document or CloudWatch Alarms Terraform config covering:

- At least **6 alerts** with assigned P0–P3 severity tiers
- Escalation path for each tier (P0: wake on-call + page manager; P1: on-call; P2: Slack + ticket; P3: ticket only)
- At least **1 suppression rule** for a realistic alert-storm scenario (e.g., "suppress P2 model drift alerts during scheduled retraining window")

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| ≥6 alerts with severity tiers | 8 | All 6 alerts have P-tier assigned; distribution across P0–P3 is reasonable |
| Escalation paths documented | 4 | Each severity tier has a named escalation action |
| ≥1 suppression rule | 3 | Suppression rule names the condition and the alerts it suppresses |

### Task 4 — SLO Design (15 points)

Define SLOs for the NorthStar churn prediction model in `docs/lab6-runbook.md`.

**Required SLOs** (all four):

| SLO | Target | SLI (Good Events / Total Events) | Error Budget | Deployment Freeze Trigger |
|-----|--------|----------------------------------|-------------|--------------------------|
| Availability | 99.5% | Successful predictions / total requests | | |
| Latency (p95) | **< 20 ms** (`ModelLatency` ≤ `20000`) | Requests completing < 20 ms / total requests | | |
| Prediction Quality | Recall@10% ≥ 0.25 on weekly sample | Weekly sample passing threshold / total weekly samples | | |
| Fairness | Recall gap across loyalty tiers ≤ 10pp | Weeks within fairness threshold / total weeks | | |

Fill in the Error Budget (in minutes/month or events/month) and the Deployment Freeze Trigger for each SLO.

> **Why the prediction-quality target is 0.25 and not something rounder.** With roughly 22% positives in the population, scoring only the top 10% caps achievable recall near **0.45** — you cannot retrieve more churners than fit in the decile you are allowed to contact. The Lab 3 reference model achieves **0.3106** (`train_reference.py`, measured 2026-08-02, registry v4), and Lab 4's promotion gate is **≥ 0.25**. Setting the SLO above the gate that let the model ship would put it in breach on the day it launched. An SLO your system fails at launch is not a target; it is a broken alarm you will learn to ignore.

> **Why the latency SLO is 20 ms while the Task 1 alert fires at 200 ms.** These are different numbers doing different jobs, and conflating them is the most common SLO mistake in industry. An **SLO** is a promise measured over a month and spent down as an error budget. An **alert threshold** is the point at which you wake a human. Measured steady-state p95 on this endpoint is ~4.15 ms, so a 200 ms SLO would be met 48x over — free, unbreachable, and it would teach you nothing. At 20 ms you keep a healthy ~5x margin, but the ~24,000 µs cold start on every deployment *does* breach it. That is the intended lesson: your own deploys consume your error budget, which is precisely why error budgets govern deployment freezes.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 4 SLOs complete with error budgets | 10 | Each row has a numeric error budget |
| Deployment freeze triggers are actionable | 5 | Each trigger is a specific condition (not "if SLO is at risk") |

### Task 5 — Runbooks (20 points)

Write complete runbooks for **two** failure scenarios in `docs/lab6-runbook.md`. Choose from:
- A: Data drift detected (PSI > 0.2 on `days_since_last_purchase`)
- B: Inference latency spike (p95 > 500 ms — `ModelLatency` > `500000` — for > 5 minutes)
- C: Feature Store unavailable (online store read failures)
- D: Fairness guardrail breach (recall gap exceeds 10pp between loyalty tiers)

**Each runbook must follow this structure:**

```markdown
## Runbook: [Failure Mode Name]

### Detection
- Alert name and threshold that triggers this runbook
- Secondary signals that confirm the failure

### Triage (< 5 minutes)
- Step 1: [specific action]
- Step 2: [specific action]

### Containment Options
- Option A: [what it does, when to choose it]
- Option B: [what it does, when to choose it — e.g., graceful degradation fallback]

### Escalation
- Trigger for escalating beyond on-call: [specific condition]
- Who is paged: [role, not person]
- SLA for response: [minutes]

### Resolution Verification
- How do you confirm the issue is resolved?
- What metric must return to normal range?

### Post-Incident Actions
- Within 24 hours: [specific action]
- Postmortem required: [yes/no — state the condition that requires one]
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Both runbooks complete with all sections | 10 | No section is "TBD" or empty |
| Containment options include a graceful degradation fallback | 6 | At least one option describes what the system does when it cannot recover immediately |
| Resolution verification is observable | 4 | Names a specific metric or CloudWatch alarm state, not "the system feels normal" |

## Traps Already Mapped — do not rediscover

These cost previous runs of this course real time and real money. They are not hypothetical.

1. **PSI and KS move in opposite directions.** PSI is a statistic (drift when `>` threshold); Evidently reports KS as a p-value (drift when `<` threshold). One comparison operator cannot serve both, and getting it wrong reports *no drift on maximally drifted data* without erroring. Verified 2026-08-07.
2. **Processing-job quota defaults to 0 for every non-burstable instance.** Not low — zero. Only `ml.t3.{medium,large,xlarge}` have a non-zero default. Endpoint, training and processing quotas are three separate numbers per instance type; one being fine says nothing about the others. `ml.t3.medium` is sufficient for Evidently. Verified 2026-07-31.
3. **`ModelLatency` is in microseconds.** 200 ms is `200000`. Every latency threshold in this lab depends on this. Verified both directions on AWS: `200000` stayed `OK`, `1000` alarmed in under a minute.
4. **Cold start is ~6x steady-state latency** (~24,000 µs vs ~4,150 µs). An alarm with `EvaluationPeriods: 1` trips on your own deployment.
5. **Endpoint configs are immutable.** Data capture cannot be added to a running endpoint; you must roll a new config.
6. **Endpoints bill hourly until deleted.** Rolling back to weight 0 does not stop the charge.
7. **Any timer you build outlives your endpoint.** SageMaker monitoring schedules are closed to you, but an EventBridge rule or cron loop you write yourself has exactly the same failure mode: it keeps launching billable processing jobs after the endpoint is gone. If you automate the drift run, delete the trigger explicitly.
8. **Burstable instances cannot be auto-scaling targets** (carried from Lab 5).
9. **IAM propagation lag ~30 s** — re-running immediately shows the *old* error and looks like your fix failed.
10. **Non-ASCII in AWS-facing `description` fields** — some services reject em dashes, others accept them, so failures look arbitrary.
11. **Console Resource Explorer lags hours.** Verify against the live API.
12. **Auto-scaling does NOT orphan scalable targets** on endpoint deletion. Verified. Do not "fix" this non-problem.

## Teardown (required — read before you submit)

**Teardown is a gate, not a rubric line.** An endpoint or drift-automation trigger still running after the deadline is a **10-point deduction**, applied on top of the gate.

```bash
bash scripts/teardown-lab6.sh
```

Order matters. Stop **any timer or in-flight processing job first**, then delete the endpoint. Anything on a schedule keeps launching processing jobs that bill on their own instances, and it will happily do so long after the endpoint it was pointed at is gone.

Teardown must remove, at minimum:
- Any EventBridge rule or cron trigger you built to automate the drift run
- In-flight processing jobs
- The endpoint, endpoint config, and both SageMaker Models
- CloudWatch alarms created for Task 1 and Task 3
- Any scaling target left from Lab 5

Then confirm with an independent all-region sweep, as in Labs 2–5. Custom CloudWatch metrics cannot be deleted — they expire after 15 months of no data. That is expected; the $0.30 metric-month charge is already accounted for.
