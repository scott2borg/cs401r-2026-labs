# Pre-Lab 3 — Bedrock Model Access Setup

**Assigned:** Thu Sep 17 (with Lab 2) | **Due:** Wed Sep 30, before Lab 3 opens
**Effort:** ~30 minutes of your time, then waiting on AWS
**Counts toward:** Lab 3 Task 4 (Repository Quality). Lab 3 Track B and C cannot start without it.

Lab 3 Track B and Track C require Amazon Bedrock. Access is **opt-in and not instant** — it involves a one-time form, per-model enablement, and possibly quota increases that AWS reviews on its own schedule. Until you enable a model, every Bedrock inference quota on your account reads **zero**, regardless of how old the account is.

Do this while you are working on Lab 2. Do not wait until Lab 3 is assigned.

## Why this is a graded exercise and not a footnote

Model entitlement and capacity approval are standard enterprise procurement problems. The lead time is not yours to control, which is exactly why platform teams begin vendor onboarding well before a launch date rather than discovering the constraint during integration.

You are also going to be asked to justify the capacity you request. "How many tokens per minute does this workload actually need, and what happens at 30x?" is a question a platform engineer answers routinely, and it is the same reasoning Lab 7 applies to platform cost. Requesting a number you cannot defend is the thing this exercise exists to prevent.

---

## What "no access" actually looks like

You will not get a clean "access denied." You get two different misleading errors, and knowing which one you have tells you what to fix.

### Error 1 — Anthropic use-case form not submitted

```
ResourceNotFoundException: Model use case details have not been submitted
for this account. Fill out the Anthropic use case details form before using
the model. If you have already filled out the form, try again in 15 minutes.
```

This blocks **every Anthropic model** regardless of quota. Fix: Step 1 below.

### Error 2 — quota is zero

```
ThrottlingException: Too many tokens per day, please wait before trying again.
```

This message is actively misleading. It does not mean you used your allowance. It means your allowance **is zero**.

Bedrock is **opt-in per model**. Until a model is enabled on the Model access page, you have no entitlement to it, and AWS expresses "no entitlement" as a quota of zero — then reports that zero as throttling. This has nothing to do with how new your account is or how much you have spent; an account five years old that has never enabled Bedrock behaves identically.

Waiting will not help. Fix: Steps 2 and 3 below.

---

## Background: how Bedrock access works now

**The Bedrock "Model access" console page was retired on 2025-10-08.** Any tutorial telling you to go there and tick boxes is out of date, including older versions of this document.

Access now works like other AWS services:

- **All serverless models are enabled by default.** There is nothing to request for Amazon, Mistral, Meta, DeepSeek, Qwen, or OpenAI models.
- **Third-party models auto-subscribe on first invocation.** Bedrock initiates an AWS Marketplace subscription in the background the first time you call the model.
- **Anthropic models additionally require a one-time First Time Use (FTU) form**, once per account (or once per AWS Organization management account).

**Prerequisites for auto-subscription to succeed:**

| Prerequisite | Detail |
|---|---|
| AWS Marketplace IAM permissions | `aws-marketplace:Subscribe`, `Unsubscribe`, `ViewSubscriptions` — needed only for the first invocation in the account |
| Valid payment method | Your account must have one configured for Marketplace purchases |
| Anthropic FTU form | Required before the first Anthropic invocation |

If a prerequisite is missing you get `AccessDeniedException`, not a helpful message.

---

## Step 1 — Submit the Anthropic use-case form

Two ways. Pick either.

### Option A — Console

Bedrock console → **Model catalog** → select any Anthropic model → open in **Playground**. You will be prompted for use case details on first use. Fill in and submit.

### Option B — API (scriptable, verified working)

```python
import boto3, json
bedrock = boto3.client("bedrock", region_name="us-east-1")

form = {
    "companyName": "Brigham Young University",
    "companyWebsite": "https://cs.byu.edu",     # a GitHub or portfolio URL is fine
    "intendedUsers": "0",                        # 0=Internal, 1=External, 2=Both
    "industryOption": "Education",
    "otherIndustryOption": "Higher Education",
    "useCases": "University coursework: retrieval-augmented offer generation and a "
                "customer-service agent over synthetic retail data. No production traffic, "
                "no real personal data.",
}
bedrock.put_use_case_for_model_access(formData=json.dumps(form).encode())
```

Field limits: `companyName`/`companyWebsite`/`industryOption`/`otherIndustryOption` ≤128 chars, `useCases` ≤8192.

Verify it registered:

```python
bedrock.get_use_case_for_model_access()   # raises ResourceNotFoundException if not submitted
```

**Note for CLI users:** `aws bedrock put-use-case-for-model-access` requires **AWS CLI ≥ 2.27.42**. On older versions these subcommands are silently absent — `aws --version` to check. The Python SDK path above has no such requirement.

---

## Step 2 — Create the model agreement

For **Anthropic models only**, after the FTU form:

```python
MID = "anthropic.claude-haiku-4-5-20251001-v1:0"
offers = bedrock.list_foundation_model_agreement_offers(modelId=MID, offerType="ALL")["offers"]
bedrock.create_foundation_model_agreement(offerToken=offers[0]["offerToken"], modelId=MID)
```

This accepts the applicable End User License Agreement. Returns HTTP 202; the agreement goes `PENDING` then `AVAILABLE`, typically within **about a minute**.

Check status:

```python
bedrock.get_foundation_model_availability(modelId=MID)
# agreementAvailability.status == "AVAILABLE" means access exists
```

**Amazon models such as Titan need no agreement** — `list_foundation_model_agreement_offers` returns *"Agreement not supported for this model"*, which is expected and not an error.

---

## Step 3 — Check your inference quota

Entitlement and quota are **separate things**. You can hold a valid agreement and still be unable to invoke anything.

```bash
aws service-quotas list-service-quotas --service-code bedrock \
  --query "Quotas[?contains(QuotaName, 'Titan Text Embeddings V2') && contains(QuotaName, 'per minute')].[QuotaName,Value,Adjustable]" \
  --output table
```

**If the values are non-zero, you are done — skip to Step 4.** This is the expected case for an established account.

**If they are zero**, note that the on-demand per-model inference quotas are marked **`Adjustable: False`**. You cannot raise them through Service Quotas; the request form will not accept them. A zero here means the account has no inference allowance at all, which shows up at invocation time as:

```
ThrottlingException: Too many tokens per day, please wait before trying again.
ThrottlingException: Too many requests, please wait before trying again.
```

Both messages are misleading. Neither means you exceeded a limit — it means your limit is zero. Waiting does not help.

**If you are in this state, open an AWS Support case** (Account and billing → Service limit increase → Bedrock), stating that your account shows zero on-demand inference quota for the models you need and that the quotas are not adjustable via Service Quotas. Include your account ID and region.

**This is the step with unpredictable lead time**, and it is why this exercise is assigned two weeks before Lab 3 rather than during it. Report the outcome to the instructor either way — we are tracking how long this takes across accounts.

---

## Step 4 — Verify, do not assume

Run this. It is the only evidence that matters.

```bash
python3 - <<'EOF'
import boto3, json, botocore
cfg = botocore.config.Config(retries={"max_attempts": 1})
rt = boto3.client("bedrock-runtime", region_name="us-east-1", config=cfg)

# Embeddings
try:
    r = rt.invoke_model(modelId="amazon.titan-embed-text-v2:0",
                        body=json.dumps({"inputText": "30 day return policy"}))
    dim = len(json.loads(r["body"].read())["embedding"])
    print(f"PASS  Titan embeddings        dim={dim}")
except Exception as e:
    print(f"FAIL  Titan embeddings        {type(e).__name__}: {str(e)[:120]}")

# Generation - note the inference profile ID, not the bare model ID
try:
    r = rt.converse(modelId="us.anthropic.claude-haiku-4-5-20251001-v1:0",
                    messages=[{"role": "user", "content": [{"text": "Reply with OK"}]}],
                    inferenceConfig={"maxTokens": 10})
    print(f"PASS  Claude Haiku 4.5        {r['output']['message']['content'][0]['text'].strip()!r}")
except Exception as e:
    print(f"FAIL  Claude Haiku 4.5        {type(e).__name__}: {str(e)[:120]}")
EOF
```

Both must print `PASS`. Save the output — it is your deliverable.

---

## Gotcha: Claude requires an inference profile ID

This one wastes an afternoon.

```python
# WRONG - raises ValidationException about on-demand throughput
modelId = "anthropic.claude-haiku-4-5-20251001-v1:0"

# RIGHT - inference profile, note the us. prefix
modelId = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
```

Anthropic models on Bedrock are `INFERENCE_PROFILE` only — there is no on-demand throughput against the bare model ID. List what is available to you:

```bash
aws bedrock list-inference-profiles \
  --query 'inferenceProfileSummaries[?contains(inferenceProfileId, `haiku`)].[inferenceProfileId,status]' \
  --output text
```

Use whichever profile shows `ACTIVE`. Both `us.` and `global.` prefixes exist; `us.` keeps inference inside US regions, which is the right default for a retailer handling US customer data — and is the kind of decision you should be able to justify, not just copy.

---

## Checking your quotas from the CLI

Faster than the console once you know what to look for:

```bash
aws service-quotas list-service-quotas --service-code bedrock \
  --query "Quotas[?contains(QuotaName, 'Titan Text Embeddings V2')].[QuotaName,Value]" \
  --output table
```

A value of `0.0` means blocked. Anything above zero means you have headroom.

---

## Cost

Bedrock is pay-per-token with no idle charge — unlike a NAT Gateway or a SageMaker endpoint, nothing bills when you are not calling it.

Realistic Lab 3 Track B usage: embedding a 4,000-word corpus a few dozen times during development, plus a few hundred generation calls for RAGAS evaluation. **Well under $2 total.** Track C is similar.

There is no teardown step for Bedrock. There is nothing left running.

---

## If you are still blocked

Escalate early, not the night before the deadline.

1. Re-run the Step 4 verification and capture the exact error text
2. Check whether it is Error 1 (form) or Error 2 (quota) using the descriptions above
3. If quota: check the Service Quotas case status — requests can sit in review
4. Contact the instructor **with the error output**, not just "Bedrock doesn't work"

**There is no course-managed fallback account.** Every student onboards their own account, which is the realistic case — you will not have a platform team doing this for you at a first job either.

If your quota request is genuinely stuck past the due date, contact the instructor with the case ID and the error output. Track A of Lab 3 requires no Bedrock at all and is worth 35 points, so a delayed approval does not block you from starting the lab. Plan the sequencing accordingly rather than treating it as an emergency.

---

## Deliverable

Submit `docs/bedrock-access-verification.txt` **by Wed Sep 30**, containing:

1. The Step 4 verification output showing both `PASS` lines
2. The output of the quota check for both models, showing non-zero values
3. One short paragraph: which quota increases you requested, what values, and your reasoning for the numbers you chose

Point 3 is the real assignment. Anyone can click "request increase." Being able to state *how much capacity your workload needs and why* is capacity planning, and it is the same reasoning you will use in Lab 7 when you cost the platform out.
