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
