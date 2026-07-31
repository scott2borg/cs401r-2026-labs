# Lab 4: XOps + CI/CD Pipeline + Testing

**Assigned:** Thu Oct 15 | **Due:** Sat Oct 31, midnight
**Chapters:** *XOps Stack*, *Testing & Evaluation*, *Continuous Delivery*
**Builds on:** Labs 1–3 — automates the lifecycle of your Lab 3 churn model

## Objective

Automate everything. A model that requires manual steps to test, evaluate, and deploy is not a production system — it is a science project. This lab builds the pipeline that takes a code commit all the way to a model approved for deployment, without human intervention in the happy path.

## Starter Kit (Canvas: Lab 4)

- `buildspec.yml` — CodeBuild build specification skeleton
- `pipeline.yaml` — CodePipeline definition starter
- `tests/test_data.py`, `tests/test_features.py`, `tests/test_model.py` — populated pytest suites covering the processed dataset, the Lab 2 feature functions, and the Lab 3 model contract. Several assertions are left as `TODO` for you to implement.

## Tasks

### Task 1 — Test Suite (30 points)

Build a test suite that runs automatically in CI. Tests must be executable via `pytest tests/` from the repo root.

**Required test categories:**

**Data validation tests** (`tests/test_data.py`):
- Schema check: all required columns present across raw, processed, and features
- Grain check: processed data stays at transaction level (many rows per customer)
- Leakage check: `churn_label` is not perfectly separable by recency alone
- Distribution checks: bounded features within [0, 1]; frequency windows monotonic (180d ≥ 90d ≥ 30d)
- Freshness check: latest `event_time` < 48 hours old

> **A missing dataset must FAIL, not skip.** The supplied `test_data.py` fails loudly when it cannot find pipeline output, and requires `ALLOW_MISSING_DATA=1` to defer. If you weaken that, `pytest tests/` goes green having validated nothing, and your Task 2 pipeline gate becomes decorative.

**Feature engineering unit tests** (`tests/test_features.py`):
- At least 5 unit tests for feature computation functions
- Cover: normal case, boundary case (customer with 0 purchases), edge case (single transaction)

**Model evaluation test** (`tests/test_model.py`):
- AUC-ROC ≥ 0.72 on held-out validation set
- Precision@top10% ≥ 0.50 and recall@top10% ≥ 0.25
- **Baseline gate: AUC must exceed the recency-only baseline by ≥ 0.03.** Your training script has to emit `baseline_auc_roc` alongside `auc_roc` for this to be checkable. This is the gate that stops a model that has learned nothing beyond "days since last purchase" from reaching the registry.
- Regression test: new model AUC ≥ (champion model AUC − 0.02)
- Prediction shape: output is a probability between 0 and 1 for every input

**Fairness check** (`tests/test_fairness.py`):
- Use SageMaker Clarify or a manual slice evaluation
- Flag (do not block) if recall gap between highest and lowest loyalty tier exceeds 10 percentage points

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 4 test categories implemented | 12 | Each category has ≥2 passing tests |
| ≥5 feature unit tests with edge cases | 10 | Tests cover normal, boundary, and edge cases |
| Regression test compares against champion | 8 | Test retrieves champion AUC from Model Registry and fails if new model regresses |

### Task 2 — CI/CD Pipeline (30 points)

Implement a CI/CD pipeline that connects: **code push → test → build → evaluate → register**.

**Acceptable implementations:** AWS CodePipeline, GitHub Actions, or GitLab CI (your choice — document the rationale).

**Required pipeline stages:**

1. **Source** — triggered by push to `main` branch
2. **Test** — runs `pytest tests/`; pipeline fails and alerts if any test fails
3. **Build** — packages training code; runs SageMaker Training Job with the new code
4. **Evaluate** — runs evaluation tests against the new model; compares to champion
5. **Register** — promotes model to SageMaker Model Registry with status `PendingManualApproval` if all gates pass

**Gate behavior:**
- Pipeline must halt at the failed stage — not silently skip
- A failed evaluation gate must send a CloudWatch alarm (email notification acceptable)

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 5 stages present and sequenced correctly | 12 | Pipeline YAML/config shows all stages; TA can trigger a run |
| Pipeline halts correctly on test failure | 10 | TA introduces a deliberate test failure; pipeline stops at Test stage |
| Model Registry promotion only on green gates | 8 | Model Registry shows `PendingManualApproval` only after a clean run |

### Task 3 — MLOps Configuration (20 points)

Document and implement the MLOps configuration for the churn model lifecycle.

**Required artifacts** in `pipeline/` or `docs/lab4-xops-assessment.md`:

- **Champion-challenger definition**: When is a new model "better enough" to replace the champion? Write the numeric criterion.
- **Retraining triggers**: Define (a) a scheduled trigger (e.g., weekly) and (b) a performance-based trigger (e.g., AUC drops below threshold on production data). Both must be automatable — not manual decisions.
- **Experiment tracking**: Show SageMaker Experiments or MLflow tracking at least 3 hyperparameter combinations with their metrics. Include a screenshot or CLI output.
- **Model lineage**: For each model version in the Registry, the associated training data version (S3 URI + timestamp), code commit SHA, and evaluation metrics must be stored as model card metadata.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Champion-challenger criterion is numeric and binary | 5 | Criterion is a specific number, not "if it is better" |
| Both retraining triggers defined and automatable | 8 | Each trigger has a specific threshold and names the AWS service that would fire it |
| Experiment tracking shows ≥3 runs | 4 | Screenshot or output confirms ≥3 trials in SageMaker Experiments |
| Model lineage metadata stored in Model Registry | 3 | `describe_model_package()` output shows training data URI and commit SHA |

### Task 4 — XOps Maturity Assessment (20 points)

Write a ~400-word maturity assessment in `docs/lab4-xops-assessment.md`.

For **DataOps** and **MLOps** (the two disciplines you have implemented so far), assess your NorthStar platform against the Level 0–4 maturity model from the chapter.

**Structure:**

```markdown
## DataOps Maturity
Current level: [0/1/2/3/4]
Evidence: [Specific artifacts from Labs 1–4 that support this assessment]
Gap to Level [N+1]: [What is the specific missing capability?]
Top priority investment: [One concrete change that would advance maturity]

## MLOps Maturity
[Same structure]
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Maturity level supported by specific evidence | 10 | Assessment references specific files/configs in the repo, not generic claims |
| Gap analysis is specific, not vague | 6 | "Missing automated drift detection (see Lab 6)" not "need more automation" |
| Priority investment is actionable | 4 | Names a specific tool or practice, not "improve testing" |
