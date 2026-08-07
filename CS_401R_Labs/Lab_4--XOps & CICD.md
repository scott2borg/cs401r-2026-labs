# Lab 4: XOps + CI/CD Pipeline + Testing

**Assigned:** Thu Oct 15 | **Due:** Sat Oct 31, midnight
**Chapters:** *XOps Stack*, *Testing & Evaluation*, *Continuous Delivery*
**Builds on:** Labs 1–3 — automates the lifecycle of your Lab 3 churn model
**Prerequisite:** *Pre-Lab 4 — SageMaker Training Quota Setup*, due Wed Sep 30. **There is no local fallback in this lab** — without the quota, the pipeline cannot complete.

## Objective

Automate everything. A model that requires manual steps to test, evaluate, and deploy is not a production system — it is a science project. This lab builds the pipeline that takes a code commit all the way to a model approved for deployment, without human intervention in the happy path.

## Starter Kit (Canvas: Lab 4)

- `buildspec.yml` — CodeBuild build specification skeleton
- `pipeline.yaml` — CodePipeline definition starter
- `tests/test_data.py`, `tests/test_features.py`, `tests/test_model.py` — populated pytest suites covering the processed dataset, the Lab 2 feature functions, and the Lab 3 model contract. Several assertions are left as `TODO` for you to implement.
- `tests/conftest.py` — registers `--model-path` and `--eval-metrics-path`. Leave it where it is; pytest only reads `pytest_addoption` from `conftest.py`.

## Before you deploy anything — four prerequisites

None of these are created for you, and each one fails in a way that does not
name the real cause. Do them first.

**1. An artifacts bucket, versioned.** CodePipeline needs a working bucket of
its own for stage artifacts. This is **not** the `northstar-dev-data-<account>`
data bucket and must not be pointed at it. Versioning is required — CodePipeline
will not use an unversioned bucket.

```bash
AB=northstar-dev-cicd-artifacts-$(aws sts get-caller-identity --query Account --output text)
aws s3api create-bucket --bucket "$AB"
aws s3api put-bucket-versioning --bucket "$AB" \
  --versioning-configuration Status=Enabled
```

**2. A GitHub connection, created and authorized *before* the stack.** A
CodeStar connection created by CloudFormation is born `PENDING`, and a
`PENDING` connection can only be completed by a human in the console — so a
stack that creates its own connection comes up "successfully" with a Source
stage that can never pull. Create it once, authorize it, then pass the ARN in.

```bash
aws codeconnections create-connection \
  --provider-type GitHub --connection-name northstar-github
# Console: Developer Tools → Settings → Connections → Update pending connection
aws codeconnections list-connections \
  --query "Connections[?ConnectionName=='northstar-github'].[ConnectionStatus,ConnectionArn]" \
  --output text
```

It must read **`AVAILABLE`** before the pipeline will run.

**3. The SageMaker Pipeline must exist.** The build triggers a pipeline named
`northstar-churn-pipeline`; a `start-pipeline-execution` against a pipeline that
was never defined fails with `ValidationException`. `pipeline_definition.py`
creates it, and the buildspec upserts it on every build so each execution is
pinned to the commit that triggered it.

**4. Deploy with `CAPABILITY_NAMED_IAM`**, not `CAPABILITY_IAM` — the template
creates named roles.

```bash
aws cloudformation deploy \
  --template-file pipeline.yaml --stack-name northstar-cicd \
  --parameter-overrides \
      ProjectName=northstar Environment=dev \
      GitHubOwner=YOUR_GITHUB_USERNAME GitHubRepo=northstar-ai-platform \
      GitHubBranch=main ArtifactsBucket="$AB" \
      GitHubConnectionArn=<arn from step 2> \
      SageMakerRoleArn=$(terraform -chdir=infrastructure/environments/dev \
                          output -raw ml_engineer_role_arn) \
  --capabilities CAPABILITY_NAMED_IAM
```

> **The training job needs on-demand training quota, and the AWS default is
> zero.** `ml.m5.large for training job usage` (`L-611FA074`) starts at **0** on
> a new account and the TrainingStep fails with `ResourceLimitExceeded`.
> **Unlike Lab 3, there is no local fallback here** — the whole point of the
> lab is that the pipeline trains, so this quota is a hard prerequisite.
>
> You should already have filed this in [[Pre-Lab 4 — SageMaker Training Quota Setup]],
> assigned back with Lab 2. If you did not, do it **now** and read Step 3 there
> for the spot-training fallback — approval is not instant and Lab 4 is two
> weeks long.
>
> ```bash
> aws service-quotas get-service-quota --service-code sagemaker \
>   --quota-code L-611FA074 --query 'Quota.Value' --output text
> ```
>
> A non-zero number is the only evidence that matters.

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
- Precision@top10% ≥ 0.50 and recall@top10% ≥ 0.25
- **Baseline gate: the 95% CI on (model AUC − recency-only baseline AUC) must exclude zero.** Your training script has to emit `baseline_auc_roc` and the CI bounds alongside `auc_roc` for this to be checkable. This is the gate that stops a model that has learned nothing beyond "days since last purchase" from reaching the registry.
- **There is deliberately no absolute AUC threshold.** A fixed AUC gate was removed on 2026-08-02: across 200 splits of the same data the reference model fell below the old 0.72 bar on 58% of them, so the gate was testing the random seed. Report AUC, gate on the interval.
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

**Required pipeline phases.** Your pipeline must perform all five of these, in
this order:

1. **Source** — triggered by push to `main` branch
2. **Test** — runs `pytest tests/`; pipeline fails and alerts if any test fails
3. **Build** — packages training code; runs SageMaker Training Job with the new code
4. **Evaluate** — runs the promotion gate against the new model's metrics
5. **Register** — promotes model to SageMaker Model Registry with status `PendingManualApproval` if all gates pass

> **Five phases is not five CodePipeline stages, and you are not required to
> make them line up.** A CodePipeline *stage* is a deployment boundary — it
> exists so artifacts can hand off and so a human can be inserted between two
> points. A CI *phase* is a logical step. Forcing one stage per phase means
> passing the model artifact between stages and standing up a CodeBuild project
> per stage, which buys nothing here.
>
> The reference implementation uses **three** CodePipeline stages:
>
> | CodePipeline stage | Phases it performs | Where |
> |---|---|---|
> | `Source` | Source | CodeStar connection → GitHub `main` |
> | `Build` | Test, Build, Evaluate, Register | `buildspec.yml`: `pre_build` runs `pytest tests/`; `build` upserts and runs the SageMaker Pipeline, which trains and registers; then the gate runs against the emitted metrics |
> | `ManualApproval` | the human promotion decision | SNS-notified approval action |
>
> Grading is on the five **phases** being present, ordered and enforced — not
> on the stage count in the console. Document your mapping either way.

**Gate behavior:**
- The pipeline must halt at the failed phase — not silently skip
- A failed gate must halt the build **and** notify. The stack creates a CloudWatch alarm `northstar-ci-build-failure` and an SNS topic `northstar-model-approvals`; subscribe an address to the topic:

```bash
aws sns subscribe --topic-arn <ModelApprovalTopicArn from stack outputs> \
  --protocol email --notification-endpoint you@example.com
```

> **Two traps in the notification path, both of which fail silently.** Wiring an
> alarm is the easy part; proving it can actually tell you something is the
> exercise.
>
> **1. `post_build` does not always run.** It runs when the *build* phase fails,
> but **not** when `pre_build` fails — CodeBuild goes straight to `FINALIZING`
> and skips it entirely. So a metric published from `post_build` is absent for
> exactly the failure the rubric asks you to demonstrate. The reference alarm
> watches `AWS/CodeBuild` `FailedBuilds`, which CodeBuild emits itself and which
> no phase failure can skip. If you publish your own metric instead, prove it
> survives a *test* failure, not just a gate failure.
>
> **2. An SNS topic policy that omits `cloudwatch.amazonaws.com` breaks
> notification without breaking the alarm.** The alarm still evaluates, still
> transitions to `ALARM`, still turns the console red — and publishes nothing.
> The only evidence is one line here:
>
> ```bash
> aws cloudwatch describe-alarm-history --alarm-name northstar-ci-build-failure \
>   --history-item-type Action --max-records 5
> # Failed to execute action arn:aws:sns:...:northstar-model-approvals
> ```
>
> Run that command against your own alarm. **An alarm that fires and cannot
> notify is worse than no alarm, because it looks like coverage.** Note also
> that SNS rejects a multi-statement topic policy unless every statement has a
> unique `Sid`.
>
> **How to demonstrate all of this:** add a deliberately failing assertion to
> `tests/`, push, and confirm four things — the run halts in the phase that owns
> tests, the Model Registry gains **no** new version, the alarm goes `ALARM`,
> and `describe-alarm-history` says *Successfully executed action*. Then revert
> and confirm the reverse: green build, registry gains a version, alarm returns
> to `OK`.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 5 phases present, ordered, with a documented stage mapping | 10 | Pipeline config plus your mapping shows all five; TA can trigger a run |
| Pipeline halts correctly on test failure | 8 | TA introduces a deliberate test failure; the run stops in the phase that owns tests and does **not** reach Register |
| Model Registry promotion only on green gates | 6 | Model Registry shows `PendingManualApproval` only after a clean run; registry gains **no** version on the failed run |
| Failure notification demonstrably delivers | 6 | On the failed run the alarm reaches `ALARM` **and** `describe-alarm-history --history-item-type Action` reads *Successfully executed action*. An alarm that fires without delivering scores 0 here |

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
