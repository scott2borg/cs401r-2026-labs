# Lab 5: Deployment & Scaling + Security

**Assigned:** Thu Oct 29 | **Due:** Sat Nov 14, midnight
**Chapters:** *Deployment & Scaling*, *Security, Privacy & Compliance*
**Builds on:** Labs 1–4 — deploys your Lab 3 churn model to production

## Objective

Ship the NorthStar churn model to production using a controlled deployment strategy, and document the security and privacy posture required to deploy customer data models in an enterprise environment. After this lab, the churn model is live. The offer generation or agent system remains in staging — it will be promoted in Lab 6 after monitoring is in place.

## Starter Kit

**None.** Labs 5–7 have no starter kit. Everything you need already exists in your repo from Labs 1–4: the trained model, the Model Registry group, the three IAM roles, and the CI/CD build. This lab is about what you do with them.

## Read This First — Cost

**This is the first lab that creates a resource billing by the hour with nothing to stop it.**

A SageMaker real-time endpoint bills from the moment it reaches `InService` until you delete it. It does not idle down, it does not expire, and nothing in SageMaker will remind you. An `ml.t2.medium` endpoint — where this lab starts — is **$0.056/hour**; `ml.m5.large` is **$0.115/hour, about $83/month**. Two variants during a canary is double that. Left running from submission day to the end of term, one forgotten endpoint costs more than the rest of this course combined.

**Rolling back does not stop the bill.** Shifting canary traffic to weight 0 stops it *serving*; the instance stays provisioned and keeps charging. Only deleting the endpoint stops the charge. Verified.

Consequences:

- The spec below requires a **compressed monitoring window** — you plan for 48 hours, you *observe* for 60 minutes. Read Task 1 carefully; do not run a literal 48-hour canary.
- Teardown is a **gate**, not a rubric line. See the Teardown section.
- An endpoint still running after the deadline is a **10-point deduction**, applied on top of the teardown gate.

## Prerequisites — do this before Task 1

Lab 4 registered your model as `PendingManualApproval`. Nothing in Labs 1–4 ever approves it, and you cannot deploy an unapproved package as a governed release.

1. **Confirm a model package exists.**

   ```bash
   aws sagemaker list-model-packages \
     --model-package-group-name northstar-churn-models \
     --query 'ModelPackageSummaryList[*].[ModelPackageVersion,ModelApprovalStatus]' --output table
   ```

   If the group is empty, re-run your Lab 3 training script to produce a version before continuing.

2. **Approve the version you intend to deploy**, and say so in your deployment plan — who approved, against which metrics.

   ```bash
   aws sagemaker update-model-package \
     --model-package-arn <arn> --model-approval-status Approved
   ```

   The approval decision is part of Task 2's pre-deployment checklist. "It was already approved" is not an answer; a human reviewed metrics and signed off, and your plan names the role that does it.

3. **If you have just torn down and re-applied Terraform:** the first `terraform apply` after a destroy fails on `aws_s3_object` refresh — the object it wants to read was removed by the destroy. Run it again. This is reproducible and expected; it is not your bug.

4. **After any IAM policy change, wait ~30 seconds before retrying.** IAM propagation lag means an immediate retry returns the *old* error and makes a correct fix look broken.

## Tasks

### Task 1 — Production Deployment (30 points)

Deploy the churn model approved above.

**Deployment approach (choose one — justify your choice in the deployment plan):**

- **Real-time endpoint** (SageMaker Real-Time Inference) — for low-latency single-record scoring
- **Batch Transform** (SageMaker Batch Transform) — for nightly batch churn scoring of the full customer base

**Requirements:**

- **Controlled rollout — not a direct swap of the endpoint config.** What this means depends on your approach:
  - *Real-time, canary:* two production variants on one endpoint, new variant at **10% initial traffic weight**, promoted to 100% after a clean monitoring window.
  - *Real-time, blue/green:* the old endpoint stays `InService` until the new endpoint passes all smoke tests, then traffic cuts over and the old endpoint is deleted.
  - *Batch Transform, parallel run:* the new model runs as a **shadow job over the same input manifest** as the incumbent; you compare score distributions and disagreement rate before the new model's output feeds anything downstream. There is no traffic weight in batch — the parallel run and the comparison artifact are what earn the points.
- **Rollback trigger configured with a numeric threshold** — specify the metric and the value. The trigger must exist **as code** in `deployment/configs/` (a CloudWatch alarm definition, Terraform resource, or deployment config), not only as prose in the plan. A threshold nobody wired up is a paragraph, not a control.

  > **`ModelLatency` is emitted in MICROSECONDS, not milliseconds.** A 200 ms threshold is `200000`. Writing `200` sets the alarm to 0.2 ms, which is far below a healthy endpoint's normal latency — measured at roughly **4,100 µs (4.1 ms)** on `ml.m5.large` for this model. The alarm goes to `ALARM` immediately and stays there, and a rollback wired to it fires against a perfectly healthy deployment. Both behaviours verified on AWS. Check the `Unit` field in `get-metric-statistics` output before you pick any threshold.

- **Rollback action.** The canary rollback is `update-endpoint-weights-and-capacities` setting the canary to weight 0. It takes about **90 seconds**, the endpoint reports `Updating` throughout but keeps serving with no dropped requests, and it does **not** stop the canary instance billing.
- **Auto-scaling policy (real-time only):** target tracking on `SageMakerVariantInvocationsPerInstance` at 1000, scale-out cooldown 60s, scale-in cooldown 600s.

  **Start on `ml.t2.medium`.** It is the cheapest real-time instance at $0.056/hr, and it is one of only three endpoint types your new AWS account has any quota for. Deploy the canary, observe the traffic split, wire the rollback alarm — all of that works.

  Then try to attach the auto-scaling policy. **It will fail**, and working out why is part of this task. See *Instance selection and quota* below before you start, so you can plan around it rather than discover it at 2am.
- **Compressed monitoring window.** Your *plan* documents the production cadence — a 48-hour canary window before promotion. Your *lab execution* observes for **60 minutes**, then promotes or rolls back. State the compression explicitly in the plan: what a 48-hour window would catch that 60 minutes cannot, and what you would additionally monitor in a real rollout. You are graded on identifying the gap, not on burning two days of endpoint time.
- **Everything deleted after the window closes and before submission.** See Teardown.

**Evidence.** CLI output is authoritative; screenshots are optional supporting material. The AWS console's resource views lag by hours and have shown deleted resources as present in this course before — do not rely on them to prove anything. Capture, in `docs/lab5-deployment-output.txt`:

1. `aws sagemaker describe-endpoint` while live, showing both variants and their traffic weights
2. `aws application-autoscaling describe-scaling-policies --service-namespace sagemaker` while live
3. The rollback alarm definition from `deployment/configs/`, plus `describe-alarms` showing its state
4. **An observed traffic split.** Invoke the endpoint at least 100 times and count the `InvokedProductionVariant` field in the responses. At 9:1 weights the reference run observed **175 champion / 25 canary over 200 calls**. This is stronger evidence than any screenshot: it proves traffic actually split, not merely that a config field was set.
5. The same count re-run after rollback, showing 0 calls to the canary
6. Post-teardown proof of no active endpoint (produced by the teardown script)

To smoke-test one variant directly without waiting for the weights to route you there, pass `--target-variant`:

```bash
aws sagemaker-runtime invoke-endpoint --endpoint-name northstar-churn-prod \
  --content-type text/csv --target-variant canary --body fileb://sample.csv out.txt
```

**Timings from the reference run**, so you can plan the 60-minute window: endpoint creation ~7 minutes, `update-endpoint` to a new config ~4 minutes (zero downtime), weight shift ~90 seconds.

#### Instance selection and quota — read this on day one, not on the due date

This part of the lab is deliberately shaped like a real production constraint. You will hit two walls in sequence. Both are real, both are survivable, and the second one has a **waiting period you cannot compress**, so start early.

**Wall 1 — burstable instances cannot be auto-scaling targets.**

You deploy on `ml.t2.medium` and everything works until you run `register-scalable-target`, which fails:

```
ValidationException: You cannot register a variant with
ml.t2.medium instance type as a scalable target.
```

This is not a bug in your configuration and there is no flag that fixes it. Burstable instances (`ml.t2.*`, `ml.t3.*`) accumulate CPU credits rather than delivering sustained performance, so Application Auto Scaling refuses to manage them — a scaling decision based on a credit-throttled instance would be meaningless. The fix is to move to a non-burstable instance type, and the obvious candidate is `ml.m5.large`.

Note what this cost you: the endpoint deployed *fine*, served traffic *fine*, and failed only at the very last step — **after it had already been billing for several minutes.** A capability you assume is available because the resource looks healthy is a category of production failure worth internalising.

**Wall 2 — your account almost certainly has zero quota for `ml.m5.large`.**

You switch the instance type, redeploy, and get:

```
ResourceLimitExceeded: The account-level service limit
'ml.m5.large for endpoint usage' is 0 Instances, with current
utilization of 0 Instances and a request delta of 1 Instances.
```

**This is expected. It is not a mistake you made.**

New AWS accounts ship with a default quota of **0** for almost every on-demand SageMaker instance type. Of 251 endpoint instance types, exactly three have a non-zero default:

| Instance type | Default endpoint quota | Auto-scaling target? |
|---|---|---|
| `ml.t2.medium` | 2 | **No** — burstable |
| `ml.m6g.large` | 2 | Yes (Graviton/ARM) |
| `ml.m6g.xlarge` | 1 | Yes (Graviton/ARM) |
| `ml.m5.large` | **0** | Yes |

AWS raises these limits as an account demonstrates usage, which is why a colleague's older account may work where your new one does not. That difference between "works on my machine" and "works on a fresh account" is exactly what breaks enterprise deployments.

**How to request the increase.**

The quota is adjustable and the request is free. It is `ml.m5.large for endpoint usage`, quota code **`L-614B09FD`**, and it is **regional** — request it in the same region you deploy to (`us-east-1` for this course).

```bash
# Check what you currently have
aws service-quotas get-service-quota \
  --service-code sagemaker --quota-code L-614B09FD \
  --region us-east-1 --query 'Quota.Value' --output text

# Request an increase. Ask for 2 - enough for a two-variant canary.
aws service-quotas request-service-quota-increase \
  --service-code sagemaker --quota-code L-614B09FD \
  --desired-value 2 --region us-east-1

# Track it
aws service-quotas list-requested-service-quota-change-history \
  --service-code sagemaker --region us-east-1 \
  --query 'RequestedQuotas[].[QuotaName,DesiredValue,Status]' --output text
```

You can also do this in the console: **Service Quotas → AWS services → Amazon SageMaker → search `ml.m5.large for endpoint usage` → Request increase at account level.**

**Ask for 2, not 20.** Small, justified requests on standard instance types are routinely approved quickly; large ones attract review and take longer. You need 2 for a two-variant canary. Asking for more delays you and costs you more if you forget a teardown.

> **Timing is the real risk in this lab.** Status moves `PENDING` → `CASE_OPENED` → `APPROVED`, and turnaround has ranged from minutes to several business days. **File this request the day the lab is assigned**, before you need it — you can do the entire `ml.t2.medium` portion of Task 1 while it is in flight. Waiting until the weekend before the deadline is the single most likely way to fail this lab for reasons that have nothing to do with your engineering.

**If your increase has not landed in time**, deploy on `ml.t2.medium`, capture the `register-scalable-target` rejection and your pending quota request as evidence, and write up the scaling design you *would* have applied. See the rubric — **this path earns full credit on the auto-scaling item.** You are graded on diagnosing and responding to the constraint, not on winning a race with AWS Support.

**A note for Lab 6.** Whatever instance you land on, **enable `DataCaptureConfig`** — Lab 6's monitoring has nothing to analyse without it, and endpoint configs are immutable so it cannot be added later without a redeploy. `ml.t2.medium` supports data capture fully, so an unresolved quota request does not block Lab 6.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Deployment approach justified in the deployment plan | 5 | Justification references NorthStar's scoring frequency requirements — not generic latency/throughput tradeoffs |
| Canary, blue/green, or batch parallel run configured (not direct swap) | 12 | **Observed** traffic split from ≥100 invocations, parallel endpoints, or a shadow batch job with a documented output comparison — not merely a config field |
| Rollback trigger defined with numeric threshold **and present as code** | 8 | Names the metric (e.g., `ModelLatency` p95) and the threshold value; a matching alarm/config exists in `deployment/configs/`; **units are correct** — a `ModelLatency` threshold of `200` instead of `200000` fails this item |
| Auto-scaling configured **or** constraint correctly diagnosed; monitoring-window compression documented | 5 | **Full credit either way.** Either (a) a scaling policy in CLI output while live on a non-burstable instance, or (b) the `ml.t2.medium` rejection captured, the burstable cause explained in one sentence, a filed quota request shown as evidence, and the intended scaling config written out. Plan states the 48h → 60min compression and what it trades away in both cases. |

### Task 2 — Operational Deployment Plan (20 points)

Write a deployment plan in `docs/lab5-deployment-plan.md` that a teammate who has never seen this project could execute. Target: 600–900 words.

**Required sections:**

1. **Deployment strategy and rationale** — why this strategy for this system?
2. **Pre-deployment checklist** — what must be true before the deployment begins? Include the model-approval step and who performs it.
3. **Rollback criteria** — exact metric, exact threshold, who makes the call
4. **Monitoring window** — how long, what you are watching, what constitutes a clean deployment, and the lab-vs-production compression from Task 1
5. **Stakeholder notifications** — who gets notified at each stage (deployment start, promotion, rollback)
6. **Post-deployment review** — when it happens, who attends, what artifact it produces
7. **Resource cleanup** — which resources are deleted after the monitoring window, in what order, and how cleanup is verified

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Document is executable by a stranger | 10 | TA review: could a new team member follow this without asking questions? Commands are copy-pasteable; no undefined names |
| Rollback criteria are numeric and unambiguous | 6 | Metric name + threshold number stated explicitly, and consistent with the alarm in `deployment/configs/` |
| Stakeholder notification list is complete | 4 | Names roles (not individuals) and what each receives at each stage |

### Task 3 — Security Assessment (25 points)

Document the security posture of the NorthStar churn model in `docs/lab5-security-assessment.md`.

**3a. STRIDE Threat Model (15 points)**

Apply STRIDE to the churn prediction system. Identify at least **five threats**, distributed across at least **3 STRIDE categories**.

| Threat | STRIDE Category | Likelihood (H/M/L) | Impact (H/M/L) | Mitigation | AWS Control |
|--------|----------------|---------------------|-----------------|------------|-------------|
| [e.g., Attacker queries endpoint to infer training data via membership inference] | Information Disclosure | Medium | High | [mitigation] | [control] |

Your platform already has a least-privilege boundary: the three IAM roles from Lab 2 — `MLEngineer` (SageMaker, Athena, features and artifacts), `DataEngineer` (Glue and data prefixes), and `ModelMonitor` (CloudWatch plus read-only artifacts). At least one threat's mitigation must reference which of these roles contains the blast radius, and at least one must identify a gap those roles do **not** close.

**3b. Data Classification (10 points)**

Classify all NorthStar data assets by sensitivity tier. For each asset specify: tier (Public / Internal / Confidential / Restricted), encryption standard (SSE-S3, SSE-KMS, or CSE), IAM access policy, and whether the asset can be shared with a third-party vendor.

Assets to classify: customer PII, transaction history, behavioral clickstream, product catalog, model weights, inference logs, Feature Store records.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| ≥5 STRIDE threats across ≥3 categories | 10 | Table complete; each row has all fields; at least one row maps to an existing Lab 2 IAM role and one names a gap |
| Mitigations reference specific AWS services | 5 | Each mitigation names the AWS service and the control — not "use encryption" |
| All 7 data assets classified | 10 | Classification table complete; SSE-KMS distinguished from S3-managed encryption with a stated reason for each choice |

### Task 4 — Privacy & Compliance Assessment (15 points)

Write a privacy impact assessment for the churn model in `docs/lab5-security-assessment.md`.

**Required sections:**

1. **Personal data inventory** — what personal data is processed, in which pipeline stage
2. **Lawful basis** — under GDPR, what is the lawful basis for processing customer purchase history for churn prediction? (Choose one: legitimate interests, contractual necessity, consent — justify your choice.)
3. **Data minimization** — what data was considered and excluded from training as unnecessary?
4. **Right to erasure workflow** — NorthStar receives a GDPR deletion request for `customer_id = C00123456`. Describe the steps to remove that customer's data from (a) raw S3 data, (b) the Feature Store, (c) the model training data, and (d) inference logs. Which step is hardest? Why?

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Lawful basis justified with specifics | 5 | Names one basis and explains why it applies to NorthStar's retention use case |
| Deletion workflow covers all 4 data stores | 6 | Each store addressed with a concrete step; the Feature Store answer distinguishes online from offline store |
| Hardest step correctly identified with reasoning | 4 | Identifies the trained model (or the offline Feature Store's append-only history) and explains why deletion there is not a delete operation |

### Task 5 — Repository Quality (10 points)

| Item | Points | Pass Criteria |
|------|--------|---------------|
| No credentials in code | 4 | `git log --all -S "AKIA"` returns nothing; `.env` is in `.gitignore` |
| Deployment config is code (not console clicks) | 3 | Endpoint config, scaling policy, and rollback alarm live in `deployment/configs/` |
| Lab 4 CI/CD extended with a security check | 3 | At least one security validation step in your pipeline definition. **`buildspec.yml` counts** — a CodeBuild phase running a secret scan, dependency audit, or IAM policy lint is full credit; you do not need CodePipeline for this |

## Traps Already Mapped — do not rediscover

1. **Endpoints bill hourly until deleted.** The trap this lab exists to teach. Rolling back to weight 0 does not stop the charge.
2. **`ml.t2.medium` cannot be an auto-scaling target.** Burstable types are rejected by `RegisterScalableTarget`. Moving to `ml.m5.large` fixes it, but that instance has a default account quota of **0** — see *Instance selection and quota* in Task 1. Both walls are expected; plan for them.
3. **`ModelLatency` is in microseconds.** 200 ms is `200000`. Normal is ~4,100 µs.
4. **The XGBoost save warning is benign.** XGBoost 3.x prints *"Saving model in the UBJSON format as default"*; the `sagemaker-xgboost:1.7-1` container loads it correctly. Verified end to end — do not go chasing this one.
5. **IAM propagation lag ~30s.** After a policy change, an immediate retry shows the old error.
6. **Non-ASCII in AWS-facing `description` / `Description` fields.** EC2 rejects em dashes, IAM accepts them, so failures look arbitrary. Keep every description ASCII-only.
7. **First `terraform apply` after a teardown fails** on `aws_s3_object` refresh. Re-run it.
8. **The console lags hours.** Verify against the live API, never the console index.
9. **Colon inside an echo string breaks buildspec YAML.** `echo "BUILD: done"` parses as a dict and CodeBuild rejects the whole file before running anything. Relevant if you edit `buildspec.yml` for Task 5.

## Teardown (required — read before you submit)

```bash
bash scripts/teardown-lab5.sh
```

The Lab 5 script deletes scaling policies and scalable targets, the rollback alarms, endpoints, endpoint configs and SageMaker models, stops in-flight jobs, then verifies against the live API and writes `docs/lab5-teardown-output.txt` — the evidence file this lab is graded on.

> **Auto-scaling does not orphan.** Deleting the endpoint automatically deregisters the scalable target, deletes its scaling policies, and deletes the `TargetTracking-*` alarms that target tracking created for you. Verified directly: registered a target, deleted only the endpoint, and all three were gone within 90 seconds. The teardown script still removes them explicitly so that the run is deterministic and the verification block means something when resources were created by hand.

Use the Lab 5 script rather than `scripts/teardown-lab3.sh`: the Lab 3 script does not delete SageMaker Models or your rollback alarms, does not assert on scaling targets, and writes to `docs/lab3-teardown-output.txt` — the wrong evidence file for this lab.

If you are also finished with the Lab 2 data platform, run `scripts/teardown-lab2.sh` afterwards — and remember `terraform destroy` alone does not fully clean up (see Lab 2's teardown section).

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Teardown evidence submitted | — | **Gate, not points:** `docs/lab5-teardown-output.txt` shows no endpoints, no endpoint configs, and no registered scaling targets. Task 1 is capped at half credit until produced. |
| Endpoint running after the deadline | −10 | Applied in addition to the gate above |
