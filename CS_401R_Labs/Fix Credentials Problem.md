# AWS Credential Troubleshooting

Common credential errors and fixes for CS 401R lab work. This course uses **personal AWS Free Tier accounts** — credentials do not rotate automatically.

---

## Error: `AuthFailure` or `InvalidClientTokenId`

Your access key is wrong or has been deactivated.

**Fix:**
1. **AWS Console → IAM → Users → cs401r-lab → Security credentials**
2. Check that your access key status is **Active**
3. If expired or deactivated, create a new one: **Create access key → CLI**
4. Reconfigure your CLI:

```bash
aws configure
# Enter your new Access Key ID and Secret Access Key
```

5. Verify:

```bash
aws sts get-caller-identity
```

---

## Error: `ExpiredToken`

You are using temporary credentials (STS/role assumption). Personal IAM user keys do not expire — this error means you accidentally configured a short-lived role session token.

**Fix:** Reconfigure with your permanent IAM user key:

```bash
aws configure
# AWS Access Key ID: AKIA... (starts with AKIA, not ASIA)
# AWS Secret Access Key: [your secret]
# Remove any AWS_SESSION_TOKEN from your environment
unset AWS_SESSION_TOKEN
```

Temporary credentials (starting with `ASIA`) come from role assumptions and expire in minutes to hours. Always use your IAM user keys (`AKIA`) for lab work.

---

## Error: `AccessDenied`

Your IAM user does not have permission for the action.

**Fix:**
1. **AWS Console → IAM → Users → cs401r-lab → Permissions**
2. Confirm `AdministratorAccess` policy is attached
3. If the error is for a specific resource (e.g., a specific S3 bucket), check whether it is in a different AWS account

---

## Error: `Could not connect to the endpoint URL` or region errors

Your CLI is pointed at the wrong region.

**Fix:**
```bash
# Check current region
aws configure get region

# Set to us-east-1 (required for all labs)
aws configure set region us-east-1

# Or use environment variable for the current session
export AWS_DEFAULT_REGION=us-east-1
```

---

## Error: `NoCredentialsError` in Python / boto3

boto3 is not finding your credentials.

**Fix:**
```bash
# Verify credentials file exists
cat ~/.aws/credentials

# Should contain:
# [default]
# aws_access_key_id = AKIA...
# aws_secret_access_key = ...
```

If the file is missing or empty, run `aws configure` again. boto3 reads from the same credentials file as the CLI.

---

## If you already use AWS for something else — named profiles

`aws configure` with no arguments writes to the `[default]` profile. If you already have AWS credentials on this machine for a job, an internship, or a personal project, **that command will overwrite them.**

Use a named profile instead:

```bash
aws configure --profile cs401r
```

Then tell every command which profile to use, either per-command or for the whole shell session:

```bash
export AWS_PROFILE=cs401r        # applies to the rest of this terminal session
aws sts get-caller-identity      # should now show YOUR course account
```

**boto3 reads `AWS_PROFILE` too**, so Python scripts pick it up with no code change. Anything in this course that works with `[default]` works identically with a named profile.

Two things to watch:

- `export AWS_PROFILE` lasts only for that terminal window. A new tab is back to `[default]`. If a script suddenly reports the wrong account, this is almost always why.
- Verify which identity you are actually using **before** creating anything billable:

```bash
aws sts get-caller-identity --query '[Account,Arn]' --output text
```

Deploying a SageMaker endpoint into the wrong account is an expensive way to discover a profile mistake.

> **Note for TAs:** the reference environment does **not** use `[default]` — it uses `AWS_PROFILE=terraform-user`. Reproducing a student's result on the reference account requires setting that explicitly. Student instructions above are correct for a fresh account and should not be changed to match the reference setup.

---

## Verify Everything is Working

```bash
# Should return your account ID and IAM user ARN
aws sts get-caller-identity

# Should return us-east-1
aws configure get region

# Should list your S3 buckets (or return empty — not an error)
aws s3 ls
```

If all three commands work, your credentials are correctly configured for lab work.
