---
created: 2026-06-24
tags: [course, labs, CS401R, AI-engineering, NorthStar]
title: "CS 401R: Lab Guide — NorthStar Retail AI Platform"
course: CS 401R
semester: Fall 2026
status: draft
---

# CS 401R Lab Guide
## Building the NorthStar Retail AI Platform

## Overview

This course has seven labs. Every lab adds a layer to the system — the **NorthStar Retail AI Platform** on AWS. By Lab 7, you will have built a complete, production-grade AI platform from scratch: infrastructure, data pipelines, models, CI/CD automation, deployment, monitoring, and business value measurement.

**This is not a toy project.** The architecture, tooling, and operational discipline you apply here is the same pattern used at enterprise scale. The standard for each lab is: *would a senior engineer at a retail company trust this in production?*

## The NorthStar Retail Scenario

**Company:** NorthStar Retail — a fictional specialty retailer operating 400 stores across North America, with a growing e-commerce presence. Annual revenue: ~$3.2B.

**AI Initiative:** NorthStar's Chief Data Officer has commissioned three AI systems to drive customer retention and lifetime value:

| System | Type | Business Goal |
|--------|------|--------------|
| **Churn Prediction** | Batch ML (XGBoost) | Predict which customers will go silent over the next 90 days; trigger retention offers |
| **Offer Generation** | LLM / RAG | Personalize retention offers using customer history and product catalog |
| **Customer Service Agent** | Agentic AI | Handle order inquiries, returns, and escalations autonomously |

All three systems share a single AWS platform. You build that platform across the seven labs.

**Data Sources (simulated):**
- `northstar-raw-sample.csv` — transaction-level purchase history: ~163,000 rows across ~11,400 customers, spanning 2025-04-01 to 2026-06-30. One row per purchase. Deliberately dirty; Lab 2 cleans it.
- `northstar-policy-docs/` — NorthStar return policy, loyalty program terms, shipping policy, and customer FAQ. The RAG corpus for Lab 3 Track B.

The transaction file spans an **observation window** (through 2026-04-01) and a **90-day holdout** after it. Lab 2 computes features from the observation window and derives `churn_label` from the holdout, which is what makes the Lab 3 churn model honest rather than circular.

*Starter data and templates are distributed on Canvas per lab.*

## Repository Structure

You maintain **one GitHub repository** for the entire semester. Each lab adds to it. Initialize it after Lab 1 is assigned. You should try to work individually as much as possible. But, if you get stuck it is fine to collaborate with your classmates. Part of the learning process is learning from others and teaching others. Use of AI is assumed and encouraged (these are the tools you will be using at work). But, you must use judgement and fully understand what is being created. 

```
northstar-ai-platform/
├── README.md                        ← Platform overview, updated each lab
├── infrastructure/                  ← Lab 1: Terraform IaC
│   ├── modules/
│   │   ├── vpc/
│   │   ├── iam/
│   │   ├── sagemaker/
│   │   └── storage/
│   └── environments/
│       ├── dev/
│       └── prod/
├── data/                            ← Lab 2: Pipelines and features
│   ├── ingestion/
│   ├── transformation/
│   └── features/
├── models/                          ← Lab 3: Model development
│   ├── churn/
│   ├── offers/
│   └── agent/
├── pipeline/                        ← Lab 4: CI/CD automation
│   ├── tests/
│   └── cicd/
├── deployment/                      ← Lab 5: Deployment and security
│   ├── configs/
│   └── security/
├── monitoring/                      ← Lab 6: Observability and reliability
│   ├── dashboards/
│   ├── alerts/
│   └── runbooks/
└── docs/                            ← Written reports, one per lab
    ├── lab1-architecture-decision-record.md
    ├── lab2-data-contract.md
    ├── lab3-model-design.md
    ├── lab4-xops-assessment.md
    ├── lab5-deployment-plan.md
    ├── lab5-security-assessment.md
    ├── lab6-runbook.md
    └── lab7-value-scorecard.md
```

**Submission:** Submit a link to your repository on Canvas before the deadline. The TA will clone your repo and run the evaluation. Late submissions incur a 10% penalty per day; a repo link that does not clone cleanly loses 20 points automatically.

**Security:** Never commit AWS credentials, access keys, or secrets. Use AWS Secrets Manager, environment variables, or `.env` files listed in `.gitignore`. Committed secrets = automatic 0 on the lab.

## Starter Kit Approach

Labs are scaffolded to fade as you progress. Early labs provide more structure; by Lab 5, you are building without templates.

**Two out-of-band prerequisites:** *Pre-Lab 3 — Bedrock Model Access Setup* is assigned with Lab 2 (Thu Sep 17) and due **Wed Sep 30**, before Lab 3 opens. On a new AWS account every Bedrock inference quota starts at zero, and access requires a one-time Anthropic use-case form plus per-model quota increases that AWS reviews on its own schedule. Lab 3 Track B and C cannot start without it; Track A is unaffected. It is graded within Lab 3 Task 4.

*Pre-Lab 4 — SageMaker Training Quota Setup* is assigned at the same time (Thu Sep 17) and also due **Wed Sep 30**, six weeks before Lab 4 opens. The AWS default on-demand SageMaker training quota is **zero instances** on a new account, so the training job Lab 4's pipeline runs fails with `ResourceLimitExceeded` until an increase is approved. **Unlike Bedrock, this one has no unaffected track** — Lab 4 cannot be completed without it. Lab 3 is only partly affected: train locally and Track A is fine. It is verified within Lab 4 Task 2.

| Lab | Data Provided | Infrastructure Templates | Code Scaffolding |
|-----|--------------|--------------------------|-----------------|
| 1 | Dataset schema + sample | Terraform module structure | None |
| 2 | Transaction dataset (dirty, ~19.5K rows) | Glue module structure | Transform + feature job skeletons |
| 3 | Policy corpus (RAG) | None | Training skeleton, evaluation harness, prompt templates |
| 4 | None | CodePipeline YAML + buildspec | Three populated pytest suites |
| 5 | None | None | None |
| 6 | None | None | None |
| 7 | None | None | None |

All starter materials are in the Canvas Lab folder for each lab.

## Grading

Each lab is graded on a **100-point scale** and weighted equally in the final grade. Rubrics are task-level; partial credit is awarded within each task.

**TA Grading Protocol:**
1. Clone the student's repo at the submission timestamp
2. Attempt to run setup instructions from the README
3. Score each rubric item independently
4. Flag any security violations for instructor review


# Lab 1: Platform Foundation

**Assigned:** Thu Sep 3 | **Due:** Sat Sep 19, midnight
**Chapter:** *AI Platform & Cloud Architecture*
**Builds on:** Nothing — this is the foundation
**Structure:** Two parts, one submission, 100 points total

## Objective

Build the NorthStar Retail AI platform skeleton on AWS — twice. First by hand in the console (Part A), then as Terraform code (Part B). The sequence is deliberate: you cannot write good Infrastructure as Code for a system you do not understand at the API level. Part A forces you to understand every resource and why it exists. Part B teaches you what IaC is actually automating.

By the end of this lab, you will have: a mental model of the platform architecture, evidence that you built it manually, and a Terraform codebase that rebuilds it from scratch with a single command.

> **Scope note:** This lab uses a single public subnet to keep the networking simple. Lab 2 adds private subnets, a NAT Gateway, and the data engineer and model monitor IAM roles — once you have context for why each of those components exists.

---

## Architecture Reference

Before touching any tool — console, CLI, or Terraform — read this specification. Every resource you create in Parts A and B corresponds to a component here.

### What the Platform Needs to Do

NorthStar's three AI systems (churn prediction, offer generation, customer service agent) all share one platform. In Lab 1, you are building the base layer that every subsequent lab depends on:

1. **A network boundary** — a VPC that isolates NorthStar's cloud resources from other AWS tenants and controls what traffic can enter and exit
2. **A storage structure** — an S3 bucket organized by data stage so different roles can only access the data they are responsible for
3. **An identity model** — IAM roles that enforce who (which AWS service) can do what (which actions) on which data
4. **A development environment** — SageMaker Studio as the IDE for all ML work in this course

### Component Specification

Use this specification to build your architecture diagram (Task A1).

---

#### Boundary: AWS Region `us-east-1`

---

##### Boundary: VPC — `northstar-dev-vpc`
- **CIDR:** `10.0.0.0/16`
- **DNS hostnames:** enabled
- **DNS resolution:** enabled

---

###### Boundary: Availability Zone `us-east-1a`

**Public Subnet — `northstar-dev-public-1`**
- CIDR: `10.0.100.0/24`
- Public IP on launch: yes
- Contains: SageMaker Studio, Internet Gateway route

---

###### VPC-Level Network Resources

**Internet Gateway — `northstar-dev-igw`**
- Attached to: `northstar-dev-vpc`
- Purpose: enables the public subnet to reach the internet (Studio needs to pull container images, reach S3, and serve the Studio UI)

**Route Table — `northstar-dev-public-rt`**
- Associated subnet: `northstar-dev-public-1`
- Routes: `0.0.0.0/0` → Internet Gateway

**Security Group — `northstar-dev-sagemaker-sg`**
- Attached to: SageMaker Domain
- Inbound: all traffic from within `10.0.0.0/16` (VPC CIDR only — no public internet inbound)
- Outbound: all traffic

---

##### Regional Service: Amazon S3

**Bucket — `northstar-dev-data-{account-id}`**
- Public access: fully blocked
- Encryption: SSE-S3 (AES-256)
- Versioning: enabled

Logical prefixes (S3 folders):

| Prefix | Purpose | Responsible Role |
|--------|---------|-----------------|
| `raw/` | Source data as ingested | DataEngineer (added Lab 2) |
| `processed/` | Cleaned, transformed data | DataEngineer (added Lab 2) |
| `features/` | Engineered feature sets | DataEngineer (added Lab 2) |
| `artifacts/` | Trained models, evaluation outputs | MLEngineer |

Create all four prefixes now. They will be used starting in Lab 2.

---

##### Global Service: AWS IAM

**Role — `northstar-dev-MLEngineer`**
- Trust: `sagemaker.amazonaws.com`
- Allowed:
  - SageMaker: training jobs, endpoints, MLflow App (experiment tracking), model registry
  - S3: read/write `artifacts/` and `features/` prefixes
  - CloudWatch Logs: write
  - ECR: read (pull training container images)
- Denied by omission: cannot write to `raw/` or `processed/`

> **Note:** `northstar-dev-DataEngineer` and `northstar-dev-ModelMonitor` roles are added in Lab 2, when the services those roles govern (Glue, Lambda, CloudWatch) are introduced.

---

##### Regional Service: Amazon SageMaker

**Domain — `northstar-dev-domain`**
- Auth mode: IAM
- VPC: `northstar-dev-vpc`
- Subnet: `northstar-dev-public-1`
- Security group: `northstar-dev-sagemaker-sg`
- Default execution role: `northstar-dev-MLEngineer`
- Notebook output sharing: disabled
- Default kernel instance: `ml.t3.medium`

**User Profile — `MLEngineer`**
- Execution role: `northstar-dev-MLEngineer`

> **Note:** Studio is placed in the public subnet in Lab 1 for simplicity. Lab 2 moves it to a private subnet with a NAT gateway for egress —the production-appropriate configuration.

---

### Connection Map (Arrows for Your Diagram)

| From | To | Direction | Label |
|------|----|-----------|-------|
| Internet | Internet Gateway | ↔ | public traffic |
| Internet Gateway | Public Route Table | → | routes |
| Public Route Table | Public Subnet | → | `0.0.0.0/0` |
| SageMaker Domain | Public Subnet | ↔ | runs in |
| SageMaker Domain | SageMaker Security Group | → | enforces |
| SageMaker Studio (MLEngineer) | MLEngineer Role | → | assumes |
| MLEngineer Role | S3 `artifacts/` | ↔ | read/write |
| MLEngineer Role | S3 `features/` | ↔ | read/write |
| MLEngineer Role | ECR | → | pull images |

---

## Starter Kit (Canvas: Lab 1)

- `northstar-scenario-overview.md` — NorthStar Retail case description
- `NorthStar_Retail_AI_Platform.pptx` — the case briefing deck
- `terraform-module-template/` — skeleton module structure for Part B: four empty modules (vpc, storage, iam, sagemaker) plus a dev environment, every variable declared and documented, every resource left as a TODO. It ships passing `terraform fmt -check -recursive` and `terraform validate`, so you start green — keep it that way, it is 5 of the 15 points in Task B1.
- `aws-account-setup.md` — AWS account setup, credit budget, and cost controls
- `northstar-data-schema.md` — data source schemas

> **New Account Bootstrap:** SageMaker Studio requires the service-linked role `AWSServiceRoleForAmazonSageMakerNotebooks`. On a brand-new AWS account, `terraform apply` may fail on the SageMaker Domain with a service-linked role error. Fix it once: **IAM → Roles → Create Role → AWS Service → SageMaker → SageMaker Studio**, then re-run `terraform apply`. This is a one-time account bootstrap, not a code error.

---

## Lab 1a: Manual Provisioning (35 points)

**Goal:** Build the platform using the AWS Console — no scripts, no IaC. This forces you to understand every resource at the API level before abstracting it.

### Pre-Flight: LocalStack Sanity Check (non-graded)

Before touching the console, run these commands against LocalStack to see the structure you are about to build:

```bash
cd northstar-ai-platform
docker compose up -d && docker compose ps

awslocal sts get-caller-identity
awslocal s3 ls s3://northstar-local-data-000000000000/ --recursive
awslocal iam list-roles --query 'Roles[?starts_with(RoleName, `northstar`)].RoleName'
awslocal ec2 describe-vpcs --query 'Vpcs[*].{Id:VpcId,CIDR:CidrBlock}'
awslocal ec2 describe-subnets --query 'Subnets[*].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}'
```

---

### Task A1 — Architecture Diagram (10 points)

Draw the diagram **before** touching the console. Use it as your build plan.

**Requirements:**
- Official AWS icons (Cloudcraft, draw.io, or aws.amazon.com/architecture/icons)
- Show VPC boundary containing the public subnet in `us-east-1a`
- Show all resources with their exact names
- Show MLEngineer role with arrows to the S3 prefixes it accesses
- Show Internet Gateway connecting the public subnet to the internet
- Legend identifying each icon type

**Deliverables:** `docs/lab1-architecture-diagram.png` and source file (`docs/lab1-architecture-diagram-source.*`)

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| VPC, public subnet, and AZ boundary correct | 3 | Matches spec — CIDR `10.0.0.0/16`, subnet `10.0.100.0/24`, `us-east-1a` |
| All resources shown with correct names | 3 | `northstar-dev-*` naming, resource types match spec |
| MLEngineer role with access arrows to S3 prefixes | 2 | Role shown; arrows to `artifacts/` and `features/` labeled correctly |
| Internet Gateway and route visible | 2 | IGW shown attached to VPC; arrow from public subnet to internet |

---

### Task A2 — Network Layer (10 points)

**Steps:**

1. **Create VPC** — Name: `northstar-dev-vpc`, CIDR: `10.0.0.0/16`, enable DNS hostnames and DNS resolution
2. **Create Public Subnet** — `northstar-dev-public-1`, AZ: `us-east-1a`, CIDR: `10.0.100.0/24`, enable auto-assign public IP
3. **Create Internet Gateway** — `northstar-dev-igw`, then attach it to `northstar-dev-vpc`
4. **Update the main route table** — add route `0.0.0.0/0` → `northstar-dev-igw`; associate `northstar-dev-public-1`
5. **Create Security Group** — `northstar-dev-sagemaker-sg`, VPC: `northstar-dev-vpc`
   - Inbound: All traffic, Source: `10.0.0.0/16` (VPC CIDR — no inbound from internet)
   - Outbound: All traffic, Destination: `0.0.0.0/0`

**Rubric:**

| Item | Points | Screenshot Required |
|------|--------|-------------------|
| VPC with correct CIDR and DNS settings | 3 | VPC console: `northstar-dev-vpc`, CIDR `10.0.0.0/16`, DNS hostnames: Enabled |
| Public subnet with correct CIDR in `us-east-1a` | 3 | Subnets list: `northstar-dev-public-1`, CIDR, AZ |
| Internet Gateway attached to VPC | 2 | IGW console: state Attached, VPC ID shown |
| Route table with IGW route associated to public subnet | 2 | Route Tables: `0.0.0.0/0 → igw-*`; subnet associations tab showing `northstar-dev-public-1` |

---

### Task A3 — Storage and IAM (10 points)

**S3 Bucket:**

1. **Create bucket** — name: `northstar-dev-data-YOUR_ACCOUNT_ID`, region: `us-east-1`
2. **Block all public access** — all four boxes checked
3. **Enable versioning**
4. **Enable SSE-S3 encryption** (AES-256)
5. **Create four folder prefixes:** `raw/`, `processed/`, `features/`, `artifacts/`

**IAM Role — `northstar-dev-MLEngineer`**

- Go to IAM → Roles → Create Role → AWS Service → SageMaker
- Role name: `northstar-dev-MLEngineer`
- Create an inline policy (name it `NorthStarMLEngineerPolicy`) with this JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "SageMakerCore",
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreateTrainingJob", "sagemaker:DescribeTrainingJob", "sagemaker:StopTrainingJob",
        "sagemaker:CreateEndpoint", "sagemaker:DescribeEndpoint", "sagemaker:DeleteEndpoint",
        "sagemaker:CreateEndpointConfig", "sagemaker:DeleteEndpointConfig",
        "sagemaker:CreateMlflowApp", "sagemaker:DescribeMlflowApp", "sagemaker:ListMlflowApps",
        "sagemaker:CreatePresignedMlflowAppUrl",
        "sagemaker:RegisterModel", "sagemaker:DescribeModelPackage", "sagemaker:ListModelPackages"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ArtifactsAndFeatures",
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::northstar-dev-data-*",
        "arn:aws:s3:::northstar-dev-data-*/artifacts/*",
        "arn:aws:s3:::northstar-dev-data-*/features/*"
      ]
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/sagemaker/*"
    },
    {
      "Sid": "ECRRead",
      "Effect": "Allow",
      "Action": ["ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage", "ecr:GetAuthorizationToken"],
      "Resource": "*"
    }
  ]
}
```

**Rubric:**

| Item | Points | Screenshot Required |
|------|--------|-------------------|
| S3 bucket: correct name, versioning enabled, SSE-S3, all public access blocked | 4 | Bucket Properties tab: Versioning Enabled, Encryption SSE-S3, Public Access all Blocked |
| All 4 prefixes visible in bucket | 3 | S3 Objects panel showing `raw/`, `processed/`, `features/`, `artifacts/` |
| `northstar-dev-MLEngineer` role with SageMaker trust and inline policy | 3 | IAM Role detail: Trust Relationships tab (sagemaker.amazonaws.com), Permissions tab (inline policy) |

---

### Task A4 — SageMaker Domain (5 points)

Start this task before finishing A2/A3 — the domain takes 8–12 minutes to provision. Let it run while you complete other steps.

**Steps:**

1. SageMaker → Domains → Create Domain → **Standard setup**
2. Name: `northstar-dev-domain` | Auth: IAM
3. Execution role: `northstar-dev-MLEngineer`
4. VPC: `northstar-dev-vpc` | Subnet: `northstar-dev-public-1` | Security group: `northstar-dev-sagemaker-sg`
5. Sharing: Notebook output sharing → Disabled
6. Submit and wait for status: **InService** (8–12 min)
7. Launch Studio → set user profile name `MLEngineer`, role `northstar-dev-MLEngineer`, instance `ml.t3.medium`
8. Verify Studio opens → immediately shut down

> ⚠️ **Shutdown required every session.** File → Shut Down → Shut Down All. Wait for Running Instances to show zero active apps. Screenshot this panel and save as `docs/lab1a-studio-shutdown.png`. Running app at submission = **−3 points, no exceptions.**

**Rubric:**

| Item | Points | Screenshot Required |
|------|--------|-------------------|
| Domain InService with correct VPC, subnet, and security group | 2 | Domain details: InService, VPC ID, subnet ID, SG ID |
| Studio opens (gates the shutdown screenshot — not graded) | — | JupyterLab UI visible |
| JupyterServer stopped; screenshot submitted | 3 | `docs/lab1a-studio-shutdown.png`: Running Instances panel, 0 active apps |

---

## Lab 1b: Infrastructure as Code (45 points)

**Goal:** Recreate Part A exactly using Terraform. Same CIDRs, same names, same policies. This codebase is your foundation for all remaining labs.

### Repo Structure

```
northstar-ai-platform/
├── infrastructure/
│   ├── modules/
│   │   ├── vpc/            # main.tf  variables.tf  outputs.tf
│   │   ├── iam/            # main.tf  variables.tf  outputs.tf
│   │   ├── storage/        # main.tf  variables.tf  outputs.tf
│   │   └── sagemaker/      # main.tf  variables.tf  outputs.tf
│   └── environments/
│       ├── dev/            # main.tf  variables.tf  tfvars.example  backend.tf  outputs.tf
│       └── local/          # main.tf  outputs.tf
├── scripts/
│   ├── bootstrap-state.sh
│   └── verify-lab1b.sh
├── docs/
├── Makefile
├── docker-compose.yml
├── .gitignore
└── README.md
```

> **Security:** Never commit credentials or `.tfvars` with real values. Grader runs `git log --all -S "AKIA"`. Automatic 0 if secrets found in git history.

---

### Task B1 — Module Structure and Code Quality (15 points)

**`modules/vpc/`** — `aws_vpc`, `aws_subnet` (public only), `aws_internet_gateway`, `aws_route_table`, `aws_route_table_association`, `aws_security_group`

**`modules/storage/`** — `aws_s3_bucket`, `aws_s3_bucket_public_access_block`, `aws_s3_bucket_versioning`, `aws_s3_bucket_server_side_encryption_configuration`, `aws_s3_object` ×4

**`modules/iam/`** — one `aws_iam_role` (MLEngineer trust), one `aws_iam_policy`, one `aws_iam_role_policy_attachment`

**`modules/sagemaker/`** — `aws_sagemaker_domain`, `aws_sagemaker_user_profile`

Code quality: all names use variables, all variables have descriptions, all modules expose needed outputs, `terraform fmt -check` and `terraform validate` both pass clean.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 4 modules present with correct resource placement | 5 | Each module contains only its designated resources |
| All names parameterized — no hardcoded literals | 5 | `grep -rn '"northstar-dev"' infrastructure/modules/` returns nothing |
| `terraform fmt` and `terraform validate` pass clean | 5 | No output from `terraform fmt -check -recursive`; validate exits 0 |

---

### Task B2 — Apply and Destroy (15 points)

```bash
# Bootstrap remote state (one-time)
bash scripts/bootstrap-state.sh

# Deploy
cd infrastructure/environments/dev
terraform init
terraform plan
terraform apply 2>&1 | tee ../../../docs/lab1b-apply-output.txt
```

Verify in the console: Domain InService, S3 bucket with 4 prefixes, VPC with public subnet, MLEngineer role. Open Studio once to confirm, then shut it down.

```bash
terraform destroy
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| `terraform apply` completes with 0 errors | 8 | `docs/lab1b-apply-output.txt` ends with `Apply complete! Resources: N added, 0 changed, 0 destroyed` |
| All resources visible in console post-apply | 4 | Screenshots: Domain InService, S3 bucket, VPC subnet, IAM role |
| `terraform destroy` completes cleanly | 3 | `terraform show` returns empty state after destroy |

---

### Task B3 — Remote State (8 points)

```hcl
# backend.tf
terraform {
  backend "s3" {
    bucket         = "northstar-tfstate-YOUR_ACCOUNT_ID"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "northstar-tfstate-lock"
    encrypt        = true
  }
}
```

`scripts/bootstrap-state.sh` must create the state bucket (versioning, SSE-S3, public access blocked) and DynamoDB lock table, patch `backend.tf` with the real account ID, and be idempotent.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| State bucket with versioning, encryption, public access blocked | 4 | `aws s3api get-bucket-versioning / get-bucket-encryption / get-public-access-block` all correct |
| DynamoDB lock table with `LockID` hash key | 2 | `aws dynamodb describe-table` returns Active |
| `bootstrap-state.sh` idempotent | 2 | Second run exits 0 with "already exists" messages |

---

### Task B4 — Parameterization (4 points)

**Required variables in `environments/dev/variables.tf`:**

| Variable | Type |
|----------|------|
| `project` | string |
| `environment` | string |
| `aws_region` | string |
| `vpc_cidr` | string |
| `public_subnet_cidr` | string |
| `availability_zone` | string |
| `sagemaker_instance_type` | string |

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 7 variables defined with descriptions | 2 | `terraform validate` passes; each has non-empty description |
| `terraform.tfvars.example` committed; `terraform.tfvars` absent from git | 2 | `git ls-files *.tfvars.example` returns file; `git ls-files *.tfvars` returns nothing |

---

### Task B5 — LocalStack Validation (3 points)

All vpc, storage, and iam resources are supported in LocalStack Community. The local environment skips only the sagemaker module.

```bash
docker compose up -d
make local-validate
```

`local-validate` must init, apply, run `awslocal s3 ls`, `awslocal iam list-roles`, and `awslocal ec2 describe-vpcs`, and save all output to `docs/lab1b-localstack-output.txt`.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| `make local-validate` exits 0; output shows S3 bucket, IAM role, VPC | 3 | All three `awslocal` commands return expected resources |

---

## Shared Deliverables (20 points)

### Task S1 — Architecture Decision Record (12 points)

Write `docs/lab1-architecture-decision-record.md` (700–1000 words):

```markdown
## ADR-001: NorthStar Platform Foundation

### Status
Accepted

### Context
[What is NorthStar building? Why does a shared AI platform need an identity model
and a storage tier structure from day one?]

### Decision
[Describe the VPC topology, S3 prefix design, and IAM role model you built.
Every rationale must tie to a NorthStar requirement — not "best practice."]

### Consequences
#### What this makes easy
#### What this makes harder
#### What would cause you to revisit this decision

### Alternative Considered
[One genuinely different approach and why you rejected it]

### AWS Service Selection
- Networking isolation model
- Storage design
- Identity model
- ML development environment
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Decision references NorthStar-specific requirements | 4 | Mentions churn scoring, LLM serving, or three-system platform — not generic reasoning |
| Consequences section is concrete | 4 | Each consequence cites a number, names a constraint, or identifies a failure mode |
| Alternative is meaningful, not a strawman | 2 | Could plausibly work; rejection reason is specific |
| AWS Service Selection covers all 4 components | 2 | One sentence per component with the deciding reason |

---

### Task S2 — Monthly Cost Estimate (8 points)

Estimate steady-state monthly cost using [AWS Pricing Calculator](https://calculator.aws):

| Component | Monthly Estimate | Key Assumptions | One Optimization |
|-----------|-----------------|----------------|-----------------|
| SageMaker Studio | $X.XX | X hrs/day at $Y/hr | |
| S3 storage | $X.XX | X GB at $0.023/GB | |
| Internet Gateway | $X.XX | $0.01/GB data transfer | |
| DynamoDB (state lock) | $X.XX | On-demand, near-zero reads | |
| S3 state bucket | $X.XX | Minimal storage | |
| **Total** | **$X.XX** | | |

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 5 components estimated | 3 | Table complete, no "TBD" |
| All assumptions explicit and plausible | 3 | Each estimate traces to a stated assumption |
| One optimization quantified | 2 | Specific change with estimated savings |

---

# Lab 2: Data & Feature Engineering

**Assigned:** Thu Sep 17 | **Due:** Sat Oct 3, midnight
**Chapter:** *Data & Feature Engineering*
**Builds on:** Lab 1 — your S3 bucket, VPC, MLEngineer role, and Terraform codebase
**Primary tool:** Terraform (all infrastructure changes are IaC from this point forward)

## Objective

Extend the NorthStar platform in two directions. First, harden the infrastructure left intentionally simple in Lab 1: move SageMaker into a private subnet behind a NAT Gateway, add the DataEngineer and ModelMonitor IAM roles, and add S3 lifecycle rules. Second, build the data pipeline that feeds the ML platform: raw data lands in S3, Glue crawls and transforms it, and engineered features are written to SageMaker Feature Store.

By the end of this lab, you will have a working end-to-end data pipeline: raw customer event data → cleaned and transformed records → feature vectors in Feature Store → ready for model training in Lab 3.

---

## What's New in Lab 2

These are additions to Lab 1's foundation. Your existing Terraform modules will be modified and extended — not replaced.

| Component | Lab 1 State | Lab 2 Change |
|-----------|------------|--------------|
| VPC networking | Public subnet only | Add private subnet + NAT Gateway; move SageMaker there |
| IAM roles | MLEngineer only | Add DataEngineer (Glue + Lambda trust) and ModelMonitor |
| S3 lifecycle rules | Deferred | Add 90-day expiration on `raw/`, version cleanup on all prefixes |
| Data ingestion | No pipeline | Glue crawler on `raw/` + ETL job → `processed/` |
| Feature engineering | No features | Glue ETL → `features/` + SageMaker Feature Group |

---

## Architecture Reference

This specification describes the **complete** Lab 2 platform — Lab 1 components plus all Lab 2 additions. Use it to build your architecture diagram before writing Terraform.

### What the Data Layer Needs to Do

The data pipeline must:

1. **Ingest raw data at rest** — customer transaction records and behavioral events land in `raw/` as CSV files
2. **Discover schema automatically** — a Glue Crawler scans `raw/` and registers the schema in the Glue Data Catalog so ETL jobs can query it without hardcoded column definitions
3. **Transform and validate** — a Glue ETL job reads from the catalog, applies type enforcement and null handling, and writes Parquet to `processed/`
4. **Engineer features and label them** — a second Glue ETL job reads `processed/`, splits it into an observation window and a holdout window, computes 13 churn-predictive features from the observation window, derives `churn_label` from the holdout, and writes to `features/`
5. **Register features for ML** — a SageMaker Feature Group ingests the feature vectors so training jobs in Labs 3–4 can pull them without re-computing
6. **Enforce data boundaries** — DataEngineer writes `raw/`, `processed/`, and `features/` but cannot write `artifacts/`; MLEngineer reads `features/` and writes `artifacts/`; ModelMonitor reads `artifacts/` and writes CloudWatch metrics only
7. **Expire stale data automatically** — raw files older than 90 days are deleted by S3 lifecycle rules

### Component Specification

---

#### Boundary: AWS Region `us-east-1`

---

##### Boundary: VPC — `northstar-dev-vpc` (extended from Lab 1)
- CIDR: `10.0.0.0/16` (unchanged)

---

###### Boundary: Availability Zone `us-east-1a`

**Public Subnet — `northstar-dev-public-1`** *(Lab 1 — no changes)*
- CIDR: `10.0.100.0/24`
- Now purpose: NAT Gateway anchor point only (Studio moved out of here)

→ Contains: **NAT Gateway — `northstar-dev-nat`** *(new in Lab 2)*
- Elastic IP: `northstar-dev-eip` (allocated, associated with NAT)
- Purpose: provides outbound internet access for the private subnet; SageMaker pulls ECR images, calls AWS APIs, reaches S3 via this path

**Private Subnet — `northstar-dev-private-1`** *(new in Lab 2)*
- CIDR: `10.0.1.0/24`
- Public IP on launch: no
- Contains: SageMaker Domain, Glue job workers

---

###### VPC-Level Network Resources

**Internet Gateway — `northstar-dev-igw`** *(Lab 1 — no changes)*

**Route Table — `northstar-dev-public-rt`** *(Lab 1 — updated association only)*
- Associated subnet: `northstar-dev-public-1`
- Routes: `0.0.0.0/0` → Internet Gateway

**Route Table — `northstar-dev-private-rt`** *(new in Lab 2)*
- Associated subnet: `northstar-dev-private-1`
- Routes: `0.0.0.0/0` → NAT Gateway
- Effect: private subnet resources reach the internet outbound; no inbound internet connections possible

**Security Group — `northstar-dev-sagemaker-sg`** *(Lab 1 — no changes)*

---

##### Regional Service: Amazon S3

**Bucket — `northstar-dev-data-{account-id}`** *(Lab 1 — extended)*
- All Lab 1 settings unchanged (versioning, SSE-S3, public access blocked)
- **New in Lab 2:** Lifecycle configuration added

Lifecycle rules *(new in Lab 2)*:

| Rule | Scope | Action |
|------|-------|--------|
| `expire-raw-data` | `raw/` | Delete current versions after 90 days |
| `expire-raw-versions` | `raw/` | Delete noncurrent versions after 30 days |
| `expire-processed-versions` | `processed/` | Delete noncurrent versions after 30 days |
| `expire-feature-versions` | `features/` | Delete noncurrent versions after 60 days |

---

##### Global Service: AWS IAM

**Role — `northstar-dev-MLEngineer`** *(Lab 1 — no changes)*

**Role — `northstar-dev-DataEngineer`** *(new in Lab 2)*
- Trust: `glue.amazonaws.com`, `lambda.amazonaws.com`, **`sagemaker.amazonaws.com`**
  (the third is required in Task 3: `CreateFeatureGroup` rejects an execution role that
  does not trust SageMaker, even though this role is otherwise a pure data-plane identity)
- Allowed:
  - Glue: full access (databases, tables, crawlers, jobs, runs) **plus `glue:GetConnection`**
  - EC2: network-interface lifecycle (`CreateNetworkInterface`, `DeleteNetworkInterface`, the `Describe*` calls) **plus `ec2:CreateTags` / `ec2:DeleteTags` on `network-interface/*`**
  - S3: read/write `raw/`, `processed/`, and `features/` prefixes
    (`features/` is required — the feature engineering job in Task 3 writes Parquet there
    and the Feature Store offline store is backed by it)
  - SageMaker Feature Store: `PutRecord`, `CreateFeatureGroup`, `DescribeFeatureGroup`
  - CloudWatch Logs: write
  - S3: read-only on `artifacts/glue/` (Glue must fetch its own job scripts)
- Denied by omission: cannot write `artifacts/`; cannot run SageMaker training jobs

**Role — `northstar-dev-ModelMonitor`** *(new in Lab 2)*
- Trust: `sagemaker.amazonaws.com`
- Allowed:
  - CloudWatch: `PutMetricData`, `GetMetricStatistics`, `PutMetricAlarm`, `DescribeAlarms`
  - SageMaker: `ListProcessingJobs`, `DescribeProcessingJob` — **read-only visibility into drift runs**
  - S3: read-only on `artifacts/` prefix
  - CloudWatch Logs: write
- Denied by omission: cannot invoke endpoints; cannot write to S3; cannot modify models; **cannot start a processing job** — that is `ModelMonitorExecution`'s job, not this one

> **This role observes; it does not act.** The distinction matters in Lab 6, where the drift analysis runs under `northstar-dev-ModelMonitorExecution` (which writes reports and pulls containers) while this role only watches. A drift alarm that cannot itself remediate is a design choice, not an oversight.

---

##### Regional Service: Amazon SageMaker

**Domain — `northstar-dev-domain`** *(Lab 1 — subnet changed)*
- Subnet: `northstar-dev-private-1` *(changed from public-1; Terraform forces replacement — ~10 min)*
- All other settings unchanged

**User Profile — `MLEngineer`** *(Lab 1 — no changes)*

**Feature Group — `northstar-dev-customer-features`** *(new in Lab 2)*
- Record identifier: `customer_id`
- Event time feature: `event_time`
- Online store: enabled (for real-time inference in Labs 3–4)
- Offline store: enabled, backed by the `features/offline-store/` prefix in S3

> **Keep the two `features/` writers apart.** The feature engineering job writes its own
> Parquet to `features/customers/`. The Feature Store offline store manages its own
> directory tree (`<account>/sagemaker/<region>/offline-store/...`) underneath whatever
> prefix you give it. Point them at the same prefix and the offline store's layout gets
> interleaved with your job output, which makes both hard to query. Use
> `features/customers/` for the job and `features/offline-store/` for Feature Store.
- IAM role: `northstar-dev-DataEngineer` (writes records); `northstar-dev-MLEngineer` (reads)
- Features — 16 definitions: 2 keys, 13 features, 1 label

| Feature | Type | Meaning |
|---|---|---|
| `customer_id` | String | Record identifier |
| `event_time` | Fractional | Unix epoch seconds — **not** an ISO 8601 string |
| `days_since_last_purchase` | Fractional | Recency at T |
| `customer_tenure_days` | Fractional | T minus first purchase |
| `purchase_frequency_30d` | Fractional | Orders in the 30 days before T |
| `purchase_frequency_90d` | Fractional | Orders in the 90 days before T |
| `purchase_frequency_180d` | Fractional | Orders in the 180 days before T |
| `avg_order_value` | Fractional | Mean order value, full history |
| `total_spend_90d` | Fractional | Spend in the 90 days before T |
| `total_lifetime_value` | Fractional | Sum of all order values |
| `avg_basket_size_6m` | Fractional | Mean items per order, last 180 days |
| `category_diversity_score` | Fractional | Distinct categories ÷ 8 |
| `online_to_store_ratio` | Fractional | 1.0 = pure online, 0.0 = pure in-store |
| `loyalty_tier` | String | Bronze / Silver / Gold / Platinum |
| `churn_risk_score` | Fractional | Rule-based recency heuristic, 0.0–1.0 — **not the label** |
| `churn_label` | **Integral** | 1 if no purchase in the holdout window, else 0 |

> **The temporal split is the point of this feature group.**
>
> ```
> |<------- observation window -------->|<--- holdout --->|
> 2025-04-01                       2026-04-01        2026-06-30
>                                       T             SNAPSHOT
> ```
>
> Every feature is computed **only** from purchases on or before `T`. `churn_label` is derived
> **only** from the holdout: 1 if the customer made no purchase in `(T, SNAPSHOT]`.
>
> Features describe the past; the label describes the future. This is the only construction
> that produces a model worth deploying. Compute recency over the full date range instead and
> it encodes the answer directly — you get a near-perfect AUC in the lab and a model that
> collapses the moment it sees real data. This is the single most common way churn models fail
> in industry, and it is why the split is baked into the lab rather than left as an exercise.
>
> `churn_risk_score` is retained deliberately and is **not** a substitute for the label. It is a
> pure recency rule, and Lab 3 requires your trained model to beat it. A model that cannot
> outperform a three-line heuristic has not earned its deployment.

> **Event time type — read this before you write the feature group.**
> SageMaker Feature Store accepts an event-time feature as either `String` (ISO 8601) or
> `Fractional` (Unix epoch seconds). This lab requires **`Fractional`**. If you declare the
> feature as `String` and then pass a numeric epoch value — or declare `Fractional` and pass
> an ISO string — `PutRecord` accepts the call and returns success, but the record never
> appears in the online store and never lands in the offline store. There is no error message.
> You will spend an afternoon debugging an empty feature group. Declare `Fractional`, and
> write `event_time` as `float(datetime.timestamp())` in the feature engineering job.

---

##### Regional Service: AWS Glue

**Catalog Database — `northstar_dev`** *(new in Lab 2)*
- Contains tables auto-discovered by the crawler and registered by ETL jobs

**Crawler — `northstar-dev-raw-crawler`** *(new in Lab 2)*
- Role: `northstar-dev-DataEngineer`
- Target: S3 `raw/customers/` prefix
- Output: table `customers` in `northstar_dev` database — the crawler names the table after the S3 prefix (`raw/customers/`) and no `TablePrefix` is set, so it is **`customers`, not `raw_customers`**
- Schedule: on-demand (run manually or trigger from ingestion)

**ETL Job — `northstar-dev-transform`** *(new in Lab 2)*
- Type: Glue Spark (Python shell for smaller datasets)
- Role: `northstar-dev-DataEngineer`
- Source: `northstar_dev.customers` (via Glue catalog)
- Transforms: type casting, null imputation, deduplication, timestamp normalization
- Sink: `processed/customers/` in S3 as Parquet

**ETL Job — `northstar-dev-feature-engineer`** *(new in Lab 2)*
- Role: `northstar-dev-DataEngineer`
- Source: `processed/customers/` in S3
- Computes: RFM features, loyalty tier, churn risk proxy score
- Sink: `features/customers/` in S3 (Parquet) + Feature Store `PutRecord` calls

---

### Connection Map (Arrows for Your Diagram)

Draw this as two layers: infrastructure (VPC/network) and data flow (S3/Glue/Feature Store).

**Infrastructure layer:**

| From | To | Direction | Label |
|------|----|-----------|-------|
| Internet | Internet Gateway | ↔ | public traffic |
| Internet Gateway | Public Route Table | → | routes |
| Public Route Table | NAT Gateway | → | `0.0.0.0/0` |
| NAT Gateway | Internet | → | outbound only |
| Private Route Table | NAT Gateway | → | `0.0.0.0/0` |
| Private Subnet | Private Route Table | → | associated |
| SageMaker Domain | Private Subnet | ↔ | runs in |
| Glue Job Workers | Private Subnet | ↔ | run in |

**Data flow layer:**

| From | To | Direction | Label |
|------|----|-----------|-------|
| Source data (external) | S3 `raw/customers/` | → | CSV upload |
| Raw Crawler | S3 `raw/customers/` | → | scans schema |
| Raw Crawler | Glue Catalog `customers` | → | registers table |
| Transform Job | Glue Catalog `customers` | → | reads |
| Transform Job | S3 `processed/customers/` | → | writes Parquet |
| Feature Engineer Job | S3 `processed/customers/` | → | reads |
| Feature Engineer Job | S3 `features/customers/` | → | writes Parquet |
| Feature Engineer Job | Feature Store `northstar-dev-customer-features` | → | PutRecord |
| MLEngineer (Lab 3+) | Feature Store | → | reads for training |

**IAM access layer:**

| Role | Resource | Access |
|------|----------|--------|
| DataEngineer | S3 `raw/` + `processed/` + `features/` | read/write |
| DataEngineer | S3 `artifacts/glue/` | read only (job scripts) |
| DataEngineer | Feature Store | write |
| MLEngineer | S3 `features/` + `artifacts/` | read/write |
| MLEngineer | Feature Store | read |
| ModelMonitor | S3 `artifacts/` | read only |
| ModelMonitor | CloudWatch | write metrics |

---

## Starter Kit (Canvas: Lab 2)

- `northstar-raw-sample.csv` — roughly 163,000 synthetic **transaction** rows across ~11,400 customers, spanning 2025-04-01 to 2026-06-30. Deliberately dirty: null `customer_id` values, duplicate `transaction_id` rows, mixed date formats, missing numeric fields, and stray whitespace — Task 2 is where you clean them. After cleaning, expect ~157,600 rows; ~10,000 customers have enough history in the observation window to carry features.

  The date range is not arbitrary. It covers an observation window (to 2026-04-01) and a 90-day holdout after it, which is what makes the churn label in Task 3 possible. About 21% of customers churn, and roughly a third of those are still buying right up to the cutoff — those are the ones a recency rule will miss.

  Schema:

  | Column | Type | Notes |
  |--------|------|-------|
  | `transaction_id` | string | `TXN-{12 alphanumeric}`. Natural key — dedup on this. |
  | `customer_id` | string | `CUST-{8 digits}`. Repeats across rows by design. |
  | `purchase_date` | date | ISO 8601, with ~3% injected in `MM/DD/YYYY` to force real parsing |
  | `order_value` | float | USD, gross. ~4% null. |
  | `num_items` | integer | Line items in the order |
  | `payment_method` | string | `credit_card`, `debit_card`, `gift_card`, `cash` |
  | `channel` | string | `store` or `online` |
  | `store_id` | string | `STORE-{3 digits}`, or `ONLINE` |
  | `product_category` | string | Primary category for the order |

  Note there is no `loyalty_tier` column: tier is *derived* from lifetime value in Task 3. Feeding it in as raw input would leak the answer.
- `glue-scripts/transform.py` — starter Glue ETL script with the schema defined and read/write wired up; the three transform functions are stubbed out
- `glue-scripts/feature_engineer.py` — starter feature engineering script with the Feature Store client wired up; the four feature computations are stubbed out
- `verify-lab2.sh` — automated rubric verification script. Run it before you submit; it checks the same assertions the TA runs.

> **Note on `generate_northstar_data.py`.** Earlier drafts of this lab shipped a five-dataset,
> multi-million-row generator (transactions, clickstream, store events, product catalog). It has
> been moved out of the Lab 2 kit to `CS_401R_Labs/_retired/` — it was never run, and its output
> does not match the schema this lab's tasks are written against. Lab 2 uses the single
> transaction CSV above so Glue runs stay under a few minutes and inside the Free Tier credit
> budget. If a later lab needs richer multi-source data, that generator is the starting point.
>
> The sample CSV is generated by `data/generate_raw_sample.py` in the reference repository
> (seeded, so it reproduces exactly). Students receive the CSV, not the generator.

---

## Tasks

All infrastructure changes in this lab are made through Terraform. Do not use the console to create or modify resources (exception: the console is fine for verifying that resources exist as expected).

---

### Task 1 — Extend Platform Infrastructure (25 points)

Modify your existing Terraform modules and apply the changes to a real AWS account.

**Changes to `modules/vpc/`:**
- Add `aws_subnet` (private, `10.0.1.0/24`, `us-east-1a`, no public IP)
- Add `aws_eip` for the NAT Gateway
- Add `aws_nat_gateway` in the public subnet, dependent on the EIP
- Add `aws_route_table` for the private subnet with `0.0.0.0/0 → aws_nat_gateway`
- Add `aws_route_table_association` for the private subnet
- Add variable `enable_nat_gateway` (bool, default true) — set to false in `environments/local/`
- Update output to expose `private_subnet_id`

**Changes to `modules/storage/`:**
- Add `aws_s3_bucket_lifecycle_configuration` with the four rules from the Architecture Reference
- Add variable `enable_lifecycle_rules` (bool, default true) — set to false in `environments/local/`

**Changes to `modules/iam/`:**
- Add `northstar-dev-DataEngineer` role, policy, and attachment
- Add `northstar-dev-ModelMonitor` role, policy, and attachment

**Changes to `modules/sagemaker/`:**
- Update `subnet_ids` in `aws_sagemaker_domain` to use the new private subnet
- Set `app_network_access_type = "VpcOnly"` so Studio egress routes through the NAT Gateway instead of straight out the Internet Gateway
- If you still have Lab 1 running, both of these force **replacement** — Terraform destroys and recreates the domain (~10 min). That is expected, not a mistake; run `terraform plan` first and confirm the replacement is the only destructive change. If you destroyed Lab 1 after submitting (as required), the domain is simply created fresh, which takes about the same time.

> **ASCII only in AWS-facing description fields.** EC2 rejects any non-ASCII character in a security group's `description` with `InvalidParameterValue: Character sets beyond ASCII are not supported`. If you pasted an em dash (—), a curly quote, or an arrow into a `description`, `terraform apply` fails at `CreateSecurityGroup` — but `terraform validate` and LocalStack both accept it, so you will not catch this until you hit real AWS. Use plain hyphens in any `description` argument that Terraform sends to an AWS API. (Confusingly, IAM *does* accept non-ASCII in policy descriptions — so the failure looks arbitrary.)

**Changes to `environments/dev/variables.tf`:**
- Add `private_subnet_cidr` (string, `"10.0.1.0/24"`)

**Apply the changes:**

```bash
cd infrastructure/environments/dev
terraform plan    # review carefully — you should see the SageMaker domain marked for replacement
terraform apply 2>&1 | tee ../../../docs/lab2-extend-output.txt
```

**LocalStack validation (update local environment):**

```bash
# environments/local/main.tf additions:
# - vpc module: enable_nat_gateway = false
# - storage module: enable_lifecycle_rules = false
# - iam module: now creates all 3 roles
make local-validate 2>&1 | tee docs/lab2-localstack-output.txt
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Private subnet + NAT Gateway created; SageMaker Domain moved to private subnet | 10 | Console: Domain InService, subnet ID matches `northstar-dev-private-1`; NAT Gateway Available |
| All 3 IAM roles exist with correct trust and policies | 8 | `aws iam list-roles` shows all 3; `iam:SimulatePrincipalPolicy` confirms DataEngineer cannot **write** `artifacts/` (read on `artifacts/glue/` is expected — Glue fetches job scripts there), ModelMonitor cannot write S3 |
| S3 lifecycle rules applied | 4 | `aws s3api get-bucket-lifecycle-configuration` returns all 5 rules: `expire-raw-data`, `expire-raw-versions`, `expire-processed-versions`, `expire-feature-versions`, `expire-datacapture` |
| LocalStack validation updated and passing | 3 | `docs/lab2-localstack-output.txt` shows 3 IAM roles; VPC exists (NAT skipped) |

---

### Task 2 — Data Ingestion Pipeline (25 points)

Build a new `modules/glue/` module and create the Glue catalog, crawler, and transform ETL job.

**New `modules/glue/` resources:**
- `aws_glue_catalog_database` — `northstar_dev`
- `aws_glue_crawler` — `northstar-dev-raw-crawler`, targets `raw/customers/` prefix, role = DataEngineer ARN
- `aws_glue_job` — `northstar-dev-transform`, Glue version 4.0, Python 3, script from S3 (upload `glue-scripts/transform.py` to `artifacts/glue/` prefix)
- `aws_s3_object` — upload the transform script as part of `terraform apply`

> **Running Glue inside the VPC — three failures you will hit in this order.**
> Because Lab 2 places Glue workers in the private subnet, the job needs a Glue
> `NETWORK` connection, and that path has three separate prerequisites. Each one fails at
> *provisioning* time with a message that does not obviously name the fix, and each only
> appears after you have cleared the previous one:
>
> 1. `DataCatalog Connection issue ... not authorized to perform: glue:GetConnection` —
>    the role needs `glue:GetConnection`. Glue resolves the connection before your script
>    ever runs, so this is not a script bug.
> 2. `At least one security group must open all ingress ports.` — Glue requires a
>    **self-referencing** all-ports ingress rule on an attached security group. An
>    equivalent rule written as the VPC CIDR does *not* satisfy the check; the source must
>    literally be the security group itself (`self = true` in Terraform).
> 3. `The specified role doesn't have a permission to create a tag for your elastic
>    network interface.` — Glue tags every ENI it creates, so the role needs
>    `ec2:CreateTags` and `ec2:DeleteTags` on `arn:aws:ec2:*:*:network-interface/*`.
>
> Also note that IAM changes take a few seconds to propagate. If you fix a policy and
> immediately re-run the job, you can see the *old* error once more — wait ~30 seconds
> before concluding your fix did not work.

**Complete the transform script** `glue-scripts/transform.py`:

The starter script defines the schema. You must implement the three transform functions:

```python
def cast_types(df):
    """Cast all columns to the types defined in SCHEMA. Drop rows where customer_id is null."""
    # Your implementation here

def impute_nulls(df):
    """
    Numeric columns: impute with column median.
    String columns: impute with 'unknown'.
    """
    # Your implementation here

def deduplicate(df):
    """
    Drop duplicate transactions: keep one row per transaction_id, taking the
    most recently loaded (by purchase_date descending) when a transaction_id
    appears more than once.

    Deduplicate on transaction_id, NOT on customer_id. A customer is expected
    to have many transactions -- that purchase history is exactly what the
    feature engineering job in Task 3 aggregates over. Collapsing to one row
    per customer here would make total_lifetime_value and purchase_frequency_30d
    impossible to compute downstream.
    """
    # Your implementation here
```

> **Why the grain matters.** `raw/customers/` holds *transaction-level* rows: one row per
> purchase, many rows per customer. The transform job preserves that grain and only removes
> genuine duplicates — the same `transaction_id` landing twice from an ingestion retry.
> Task 3 is where the data collapses to one row per customer, by aggregation. Getting this
> backwards is the single most common way to fail Task 3 after passing Task 2.

**Upload sample data and run the pipeline:**

```bash
# Upload sample data
aws s3 cp northstar-raw-sample.csv \
  s3://northstar-dev-data-$(aws sts get-caller-identity --query Account --output text)/raw/customers/northstar-raw-sample.csv

# Run the crawler (waits for completion)
aws glue start-crawler --name northstar-dev-raw-crawler
aws glue get-crawler --name northstar-dev-raw-crawler --query 'Crawler.State'

# Verify the table was created
aws glue get-table --database-name northstar_dev --name customers

# Run the transform job
aws glue start-job-run --job-name northstar-dev-transform
aws glue get-job-run --job-name northstar-dev-transform \
  --run-id $(aws glue get-job-runs --job-name northstar-dev-transform \
    --query 'JobRuns[0].Id' --output text)

# Verify processed output
aws s3 ls s3://northstar-dev-data-ACCOUNT_ID/processed/customers/ --recursive
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Glue catalog database and `customers` table exist after crawler run | 6 | `aws glue get-table --database-name northstar_dev --name customers` returns schema |
| Transform script correctly casts types, imputes nulls, deduplicates | 12 | `verify-lab2.sh` runs assertions against `processed/customers/` output: correct Parquet schema, 0 null `customer_id` rows, no duplicate `customer_id` rows |
| `modules/glue/` Terraform resources applied cleanly | 4 | Module present in repo; `terraform apply` creates crawler and job with 0 errors |
| Transform job completes with SUCCEEDED status | 3 | `aws glue get-job-run` returns `JobRunState: SUCCEEDED` |

---

### Task 3 — Feature Engineering and Labelling (20 points)

Add the feature engineering ETL job to `modules/glue/` and a new `modules/feature_store/` module.

**Add to `modules/glue/`:**
- `aws_glue_job` — `northstar-dev-feature-engineer`, reads `processed/customers/`, writes to `features/customers/` and calls Feature Store

**New `modules/feature_store/`:**
- `aws_sagemaker_feature_group` — `northstar-dev-customer-features`
  - Record identifier: `customer_id`
  - Event time: `event_time`
  - Online store: enabled
  - Offline store: S3 URI `s3://northstar-dev-data-{account-id}/features/offline-store/`
  - Execution role: DataEngineer role ARN
  - Feature definitions: all 8 features from the Architecture Reference

> **Two Feature Store permission traps, both with misleading error messages.**
>
> 1. `ValidationException: The execution role ARN is invalid` — this does *not* mean the ARN
>    is wrong. It means the role's trust policy is missing `sagemaker.amazonaws.com`. Add it
>    to DataEngineer's trusted services.
> 2. `ValidationException: Invalid S3Uri provided` — the URI is fine. The role is missing
>    `s3:GetBucketAcl` on the bucket. Feature Store checks the bucket ACL before accepting it
>    as an offline store target. You also need `s3:PutObjectAcl` on `features/*`, because the
>    offline store writes objects with an ACL and plain `PutObject` is not enough.
>
> Both fail at `terraform apply`, before any data moves, so a green `terraform validate` tells
> you nothing here.

**Anchor your time windows to the data, not to `today()`.** Compute recency and the 30-day
frequency window relative to the maximum `purchase_date` in the dataset. If you use the wall
clock, your features change every time the job runs, and any model Lab 3 trains on them stops
being reproducible.

**Complete the feature engineering script** `glue-scripts/feature_engineer.py`:

The starter script reads from `processed/customers/`. Implement these feature computations:

```python
def split_windows(df):
    """
    Split processed transactions into:
      history : purchase_date <= FEATURE_CUTOFF (T)
      holdout : FEATURE_CUTOFF < purchase_date <= SNAPSHOT
    Every feature comes from history. The label comes from holdout.
    """
    # Your implementation here

def compute_rfm_features(history):
    """
    One row per customer_id, all windows measured backwards from T:
      days_since_last_purchase, customer_tenure_days,
      purchase_frequency_30d / 90d / 180d,
      avg_order_value, total_spend_90d, total_lifetime_value,
      avg_basket_size_6m, category_diversity_score, online_to_store_ratio
    """
    # Your implementation here

def assign_loyalty_tier(df):
    """
    Bronze: total_lifetime_value < 500
    Silver: 500 <= total_lifetime_value < 2000
    Gold: 2000 <= total_lifetime_value < 5000
    Platinum: total_lifetime_value >= 5000
    """
    # Your implementation here

def compute_churn_proxy(df):
    """
    churn_risk_score: rule-based recency heuristic, NOT the label.
    High risk (0.7-1.0): days_since_last_purchase > 60 AND purchase_frequency_30d == 0
    Medium risk (0.4-0.7): days_since_last_purchase > 30
    Low risk (0.0-0.4): otherwise
    Scale within each band rather than emitting three constants.
    """
    # Your implementation here

def attach_churn_label(features, holdout):
    """
    churn_label = 1 if the customer made NO purchase in the holdout window,
    else 0. Derived exclusively from data after T.
    """
    # Your implementation here
```

**Run and verify:**

```bash
# Run feature engineering job
aws glue start-job-run --job-name northstar-dev-feature-engineer

# Verify features written to S3
aws s3 ls s3://northstar-dev-data-ACCOUNT_ID/features/customers/ --recursive

# Verify Feature Store records (after job completes — offline store has ~15 min lag)
aws sagemaker describe-feature-group --feature-group-name northstar-dev-customer-features
```

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| All 5 feature functions implemented correctly | 10 | `verify-lab2.sh` checks: no null feature values, all 4 tiers present, `churn_risk_score` in [0, 1], one row per customer |
| Temporal split correct — features from history, label from holdout | 4 | `churn_label` rate between 15% and 30%; no feature computed from post-cutoff data |
| Feature Group created via Terraform with all 16 definitions | 3 | `aws sagemaker describe-feature-group` returns 16 features; `event_time` Fractional; `churn_label` Integral; online store Enabled |
| Feature engineering job completes with SUCCEEDED status | 3 | `aws glue get-job-run` returns SUCCEEDED |

---

### Task 4 — Data Contract and Lineage (15 points)

**Data Contract** — write `docs/lab2-data-contract.md`:

A data contract is a formal agreement between the team that produces a dataset and the team that consumes it. It specifies schema, quality guarantees, and SLAs. Write one for the `processed/customers/` dataset:

```markdown
## Data Contract: processed/customers

### Producer
Team / process: Glue ETL job `northstar-dev-transform`

### Consumers
- Feature engineering job `northstar-dev-feature-engineer`
- (Future) Direct model training in Lab 3

### Schema
| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
[fill in all columns from the processed dataset]

### Quality Guarantees
- `customer_id` is never null
- No duplicate `customer_id` rows
- All numeric columns are within expected ranges (specify bounds)
- `purchase_date` is a valid ISO 8601 date

### SLA
- Data is available in `processed/customers/` within 2 hours of landing in `raw/customers/`

### Versioning
- Schema changes require a new S3 prefix (e.g., `processed/customers/v2/`)
- Breaking changes require consumer notification 5 business days in advance
```

**Data Lineage Diagram** — create `docs/lab2-data-lineage.png`:

Draw a lineage diagram showing the full flow from source to Feature Store. Include: source system → S3 `raw/` → Glue Crawler → Catalog → Transform Job → S3 `processed/` → Feature Engineer Job → S3 `features/` + Feature Store. Label each arrow with the data format (CSV, Parquet, Feature Store records) and the IAM role performing each write.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Data contract covers schema, quality guarantees, SLA, and versioning policy | 8 | All four sections present; quality guarantees include at least 3 specific, measurable assertions |
| Lineage diagram is accurate and complete | 7 | All nodes in the data flow present; formats labeled on each edge; IAM roles labeled on each write edge |

---

### Task 5 — Repository Quality (15 points)

| Item | Points | Pass Criteria |
|------|--------|---------------|
| `modules/glue/` and `modules/feature_store/` present with correct resources | 4 | All resources in correct modules; no cross-module duplication |
| All Glue and Feature Store resource names parameterized | 3 | No hardcoded strings in `.tf` files for new modules |
| `terraform fmt` and `terraform validate` pass on all modules | 3 | Clean output from both commands |
| `docs/lab2-extend-output.txt` shows a successful apply | 3 | File ends with `Apply complete!` and contains `aws_sagemaker_domain`. Either outcome is acceptable: **replacement** if you still had Lab 1 running, **creation** if you destroyed Lab 1 as instructed. Both are correct. |
| README updated to describe Lab 2 additions | 2 | README explains new modules, how to run the data pipeline end-to-end |

---

### Teardown (required — read before you submit)

**The NAT Gateway bills roughly $0.045/hour (~$32/month) whether or not you send a byte through it.** It is the single largest cost in this lab and it does not stop when you close the console. Leaving it running for three weeks will consume a meaningful share of your $200 in Free Tier credits — credits you still need for Labs 3 through 7.

After you have captured your verification output and submitted:

```bash
bash scripts/teardown-lab2.sh
```

> **`terraform destroy` alone will not tear this lab down.** Six resources are created
> outside Terraform's state and survive it. Three of them make `destroy` hang for 10+ minutes
> and then fail; one of them keeps billing after you believe you are finished.
>
> | # | Orphan | Consequence |
> |---|--------|-------------|
> | 1 | Glue ENIs left in the private subnet after job runs | Subnet and security group deletion hang |
> | 2 | **SageMaker Studio EFS filesystem** | Terraform never sees it — **it keeps billing**, and its mount target blocks the subnet |
> | 3 | Two auto-created SageMaker NFS security groups | VPC deletion hangs |
> | 4 | S3 object versions | `BucketNotEmpty` — a versioned bucket will not delete while non-empty |
> | 5 | `sagemaker_featurestore` Glue database | Left behind by the offline store |
> | 6 | SageMaker **lineage contexts and artifacts** | Survive `DeleteFeatureGroup`; refuse to delete until their associations are unwound first |
>
> `scripts/teardown-lab2.sh` handles all six in the correct order and then verifies that no
> billable resource remains. If you insist on running `terraform destroy` by hand, expect to
> clean up items 1–6 manually and to wait through two failed attempts first.
>
> **Do not trust the AWS console's Resource Explorer to confirm teardown.** Its index lags by
> minutes to hours and will keep listing resources that are already gone — and it may equally
> miss ones that remain. Verify with `aws` CLI calls against the live API, which is what
> `scripts/teardown-lab2.sh` does in its final step.
>
> Item 4 is also why `modules/storage/` sets `force_destroy` in the dev environment. That is
> the right call for synthetic, regenerable lab data and **the wrong call for a bucket holding
> real customer records** — it deletes every version with no confirmation.

Commit `docs/lab2-destroy-output.txt`. Lab 3 begins by re-running `terraform apply`, which rebuilds everything from your committed code in about 15 minutes — that rebuild is itself the proof that your infrastructure is genuinely reproducible.

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Infrastructure destroyed after submission | — | `docs/lab2-destroy-output.txt` ends with `Destroy complete!` **and** `scripts/teardown-lab2.sh` reports no billable resources remaining. **Gate, not points:** if this evidence is missing, Task 1 is capped at half credit until you produce it. |

---

# Lab 3: Model Development

**Assigned:** Thu Oct 1 | **Due:** Sat Oct 17, midnight
**Chapters:** *Model Development* (Sessions 1–3: Fine-Tuning, RAG, Agents)
**Builds on:** Lab 2 — models train on the Feature Store features and `churn_label` you produced
**Primary tools:** SageMaker (training, MLflow App, Model Registry), Bedrock
**Prerequisite:** *Pre-Lab 3 — Bedrock Model Access Setup*, due Wed Sep 30 — Tracks B and C cannot start without it.
**Prerequisite (only if training on SageMaker):** *Pre-Lab 4 — SageMaker Training Quota Setup*, due Wed Sep 30. Your on-demand training quota is **0** by default, so `CreateTrainingJob` fails until an increase is approved. Train locally instead and every Track A rubric item is still reachable.

> **If you have not completed the Bedrock setup exercise, do it now.** On a new AWS account, every Bedrock inference quota is **zero**, and access requires a one-time Anthropic use-case form plus per-model quota increases that AWS reviews on its own schedule. This is not something you can resolve the night before the deadline. Track A (35 points) requires no Bedrock and can proceed regardless. Track B and Track C cannot start without it. Sequence your work accordingly.

## Objective

Implement two of NorthStar's three AI systems. Every student builds the churn prediction model; you then choose one LLM-based system — offer generation or the customer service agent.

This is where the platform starts doing something the business would pay for. It is also where you find out whether the features you engineered in Lab 2 were worth engineering.

---

## What You Are Predicting

Lab 2 wrote a Feature Group with 13 features and one label, built on a deliberate temporal split:

```
|<------- observation window -------->|<--- holdout --->|
2025-04-01                       2026-04-01        2026-06-30
                                      T             SNAPSHOT
```

- Every **feature** was computed from purchases on or before `T`.
- `churn_label` was derived from the holdout: **1** if the customer made no purchase in `(T, SNAPSHOT]`, else **0**.

Your model predicts, from behavior observable at `T`, whether a customer will go silent over the following 90 days. Roughly **22%** of customers churn.

### The part that makes this hard

About a third of churners are **still buying right up to `T`**. Their recency looks perfectly healthy. A model that leans on `days_since_last_purchase` alone will rank them as safe and miss them entirely — and those are exactly the customers a retention program could still save. The ones who lapsed months ago are already gone; you do not need machine learning to find them.

This is why Lab 2 made you build category diversity, channel mix, and basket size. If your model cannot beat a recency rule, those features were wasted work — and the rubric checks that explicitly.

---

## Starter Kit (Canvas: Lab 3)

- `churn_training_skeleton.py` — SageMaker training entry point: Feature Store Athena query, XGBoost setup with class-imbalance handling, evaluation gates, slice-evaluation stub, Model Registry registration. Several `TODO`s are yours to complete.
- `evaluation_harness.py` — dual-track evaluation. Track B: four RAGAS test cases built from real Lab 2 features, with ground truths written against the policy corpus. Track C: the five required agent scenarios plus a bonus prompt-injection case, each with expected and forbidden tool calls and an escalation expectation.
- `prompt_templates/offer_generation_prompts.md` — five templates carrying two documented design weaknesses plus **three planted factual errors** in the tier-guidelines block. The errors are the kind a marketing team introduces when writing copy from memory: two wrong tier thresholds and one benefit that exists at no tier. Find them by diffing against the policy corpus; injecting the block unchanged will fail faithfulness.
- `northstar-policy-docs/` — the RAG corpus for Track B: return policy, loyalty program terms, shipping policy, and an FAQ.

---

## Track Selection

All students complete **Track A**. Choose **Track B or Track C** for the second system.

| Track | System | Approach |
|-------|--------|----------|
| **A (required)** | Churn Prediction | XGBoost on Lab 2's Feature Store features |
| **B (choose one)** | Offer Generation | RAG over the policy corpus using Bedrock |
| **C (choose one)** | Customer Service Agent | ReAct agent with tools, using Bedrock |

Declare your choice at the top of `docs/lab3-model-design.md` before you write code.

---

## Cost Discipline

Lab 3 introduces two new ways to spend money without noticing:

| Resource | Cost | Rule |
|---|---|---|
| SageMaker training jobs | ~$0.10–0.30 per run on `ml.m5.large` | Cheap to run — but **your quota is 0 until you request an increase.** See below. |
| **SageMaker endpoints** | **~$0.05–0.10/hour, billed until deleted** | **Delete after every test.** This is the Lab 3 equivalent of Lab 2's NAT Gateway. |
| Bedrock inference | per-token | Small at lab scale; track it in Track B/C |
| Studio kernels | ~$0.05/hour | Stop the kernel when you stop working |

**You do not need a persistent endpoint to pass this lab.** Batch transform or a local model load is sufficient for every rubric item. If you deploy an endpoint to experiment, delete it the same session. Run `bash scripts/teardown-lab3.sh` when you submit.

> **You also do not need a SageMaker Training Job to pass this lab — which is fortunate, because you probably cannot run one yet.** The AWS default on-demand training quota is **0 instances** for every family, so `CreateTrainingJob` fails with `ResourceLimitExceeded` regardless of your budget. Train locally: `churn_training_skeleton.py` runs on your machine against the Feature Store data, and every Track A rubric item is reachable that way.
>
> If you want to use a real training job here — and you will need one in **Lab 4**, which has no local fallback — file the quota request now. See [[Pre-Lab 4 — SageMaker Training Quota Setup]]. It is assigned alongside Pre-Lab 3 for the same reason: the approval time is not yours to control.
>
> One consequence worth knowing before you compare numbers: **the SageMaker training container runs XGBoost 1.7**, and this lab's reference metrics were measured on 3.2.0. See the provenance note under Task 1 — the two will not agree to four decimal places, and that is expected.

---

## Tasks

### Task 1 — Churn Prediction Model (Track A, required) (35 points)

Train a churn model on the Lab 2 Feature Store data.

**Requirements:**

- Training data comes from the **Feature Store offline store** via Athena — not a CSV export and not the `features/customers/` Parquet directly. The point is to use the feature platform you built.
- Model: XGBoost via the `sagemaker.xgboost` estimator.
- Hyperparameters (`max_depth`, `eta`, `num_round`, `scale_pos_weight`) passed as arguments, never hardcoded.
- Every training run tracked as a run in a **SageMaker MLflow App** — see *Experiment tracking* below.
- Final model registered in the **Model Registry** with status `PendingManualApproval`. Never auto-approve.
- Class imbalance handled explicitly — roughly 22% positives. Justify your `scale_pos_weight`. (Reference run derives 3.545 from the training split rather than hardcoding it.)

### Experiment tracking — use an MLflow App, and read the warning first

> ## ⚠ There are two MLflow products on SageMaker. One of them will destroy your budget.
>
> | | **MLflow App** ✅ | MLflow **Tracking Server** ❌ |
> |---|---|---|
> | API | `CreateMlflowApp` | `CreateMlflowTrackingServer` |
> | Cost | **no additional charge** | **$0.60/hr**, billed until deleted |
> | Left running one weekend | $0 | **~$43** |
>
> The course budget alarm for **all seven labs** is **$10/month**. A single forgotten tracking server breaches it in **16.7 hours** and costs four times the entire course budget in a weekend. It is not an endpoint, so `teardown-lab5.sh` will not catch it, and nothing about it looks expensive in the console.
>
> **Most search results and tutorials describe the Tracking Server**, because it shipped first. If you find yourself sizing an instance or picking `Small`/`Medium`, stop — you are on the wrong one. The App is serverless, scales to zero, and has no size to choose.

Create the App once. It takes about five minutes and you keep it for the whole course.

```bash
aws sagemaker create-mlflow-app \
  --name northstar-mlflow \
  --artifact-store-uri s3://northstar-dev-data-<account>/mlflow/ \
  --role-arn arn:aws:iam::<account>:role/northstar-dev-DataScientist \
  --query Arn --output text
```

> **`create-mlflow-app` requires a recent AWS CLI.** The API postdates many installed versions, and an old CLI reports `Invalid choice: 'create-mlflow-app'` — which reads like a typo, not a version problem. Check with `aws --version` and upgrade if the command is missing. Same applies to `boto3`/`botocore` if you call it from Python.

Poll until `Status` is `Created` (**measured: 4 min 52 s**), then point your training code at the ARN:

```python
import mlflow

mlflow.set_tracking_uri(APP_ARN)          # the arn:aws:sagemaker:...:mlflow-app/... string
mlflow.set_experiment("northstar-churn")

with mlflow.start_run(run_name="xgb-baseline"):
    mlflow.log_params({"max_depth": 6, "eta": 0.2, "num_round": 200,
                       "scale_pos_weight": 3.545})
    mlflow.log_metrics({"auc": auc, "precision_at_10pct": p10,
                        "recall_at_10pct": r10})
```

You need two packages: `mlflow` **and** `sagemaker-mlflow`. The second is the auth plugin that teaches MLflow to speak to an `arn:aws:sagemaker:...` tracking URI with SigV4. Without it you get a connection error that says nothing about credentials.

Verified 2026-08-07: an App created this way ran **MLflow 3.10.1** server-side, accepted three runs, and returned them through `mlflow.search_runs` with params and metrics intact — from a plain IAM user with **no SageMaker Studio domain**. You do not need Studio for this.

**What earns the 5 points:** three runs is the floor, not the goal. Log the hyperparameters you actually varied, and make the comparison mean something — three runs with identical params and different seeds is not an experiment, it is the same experiment three times.

**Guard against leakage.** `churn_risk_score` is a feature in the Feature Group, and it is a pure recency heuristic. You may include it, but if you do, report results **with and without it**. Do not include `churn_label` as an input, and do not construct features from post-`T` data.

**Evaluation report** — required in `docs/lab3-model-design.md`:

| Metric | Your value | Threshold |
|--------|-------|-----------|
| AUC-ROC (holdout) | | report it — **no fixed threshold** |
| Precision @ top 10% | | ≥ 0.50 |
| Recall @ top 10% | | ≥ 0.25 |
| **AUC lift over recency-only baseline** | | **95% CI must exclude zero** |

The baseline is a model trained on `days_since_last_purchase` alone. Train it, report its AUC, and show your full model beats it — **with a confidence interval on the difference, not just two numbers.** Reference implementation measured **0.7696 full vs 0.7233 recency-only, a lift of +0.0464, 95% CI [0.0254, 0.0670]**.

> **Why there is no absolute AUC threshold.** There used to be one — AUC ≥ 0.72 — and it was removed on 2026-08-02 because it was not a real gate. Measured across 200 random train/test splits of the same data, the reference model's AUC varied by ±0.03 and fell below 0.72 on **58% of splits**. A threshold that the reference implementation clears by luck of the shuffle grades your random seed, not your model. The old lift gate of ≥ 0.03 was worse: the threshold was *smaller than the metric's own standard deviation*.
>
> What replaces it is the question the lab actually asks: **did your feature engineering do measurable work?** You answer that with an interval. If the 95% CI on (your AUC − baseline AUC) excludes zero, you have evidence. If it straddles zero, you do not — regardless of how good the point estimate looks. Compute it by bootstrapping your test set: resample it with replacement ~2,000 times, score both models on each resample, and take the 2.5th and 97.5th percentiles of the difference. Resample the *rows once per replicate and score both models on them* — resampling the two models independently inflates the interval.

> **Where these numbers come from.** All reference metrics in this lab are from `models/churn/train_reference.py` — the Athena path Task 1 requires — measured end to end on 2026-08-02 against the 10,000-customer dataset (registry version v4), `seed=42`, `test_size=0.30`, 6,999 train / 3,000 test, **on XGBoost 3.2.0**. Any figure you encounter from before that date is superseded; the dataset was 8x smaller and its metrics did not reproduce.
>
> **The XGBoost version is part of that provenance, not a footnote.** These figures reproduce to four decimal places run after run *at a fixed XGBoost version*, and they move when the version changes. Measured 2026-08-03 on identical data, an identical split and an identical `scale_pos_weight`:
>
> | Metric | XGBoost 3.2.0 (above) | XGBoost 1.7 |
> |---|---|---|
> | Recency-only baseline AUC | 0.7233 | **0.7208** |
> | Precision@10% | 0.6833 | **0.6933** |
> | Recall@10% | 0.3106 | **0.3152** |
>
> This matters because **the SageMaker XGBoost training container is 1.7**, so if you train through a SageMaker Training Job — or through the Lab 4 pipeline — you should expect the third column, not the second. Nothing is wrong with your model. Report the version you trained on alongside your metrics, and compare like with like. The gate is unaffected: the lift CI excludes zero in both.

Note the recall ceiling: with ~22% positives, targeting the top 10% of customers caps recall at about **45%**. A recall of 0.25 means you are capturing roughly half of what is theoretically reachable in that budget.

Also include: confusion matrix at your chosen threshold, feature importance plot, and **slice evaluation across loyalty tiers**.

> **Report `n` alongside every slice metric, and say which slices are too small to support a claim.** This is not bookkeeping. On an earlier, 8x smaller version of this dataset the Platinum tier held about 33 test customers with roughly 2 churners, and the measured Platinum AUC swung between 0.00 and 1.00 depending only on the random split — it read as "worse than random" on about a third of splits. That reading was published as a finding, and it was wrong: at ~300 test customers Platinum is the model's *strongest* slice. A slice metric without an `n` beside it is not a measurement, and a confident conclusion drawn from ~2 positives is how a careful-looking analysis ends up exactly backwards.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Training data pulled from Feature Store offline store via Athena | 5 | Training script issues an Athena query against the offline store table; no CSV path in the data-loading code |
| Model meets precision and recall thresholds | 8 | Both met on a held-out split; AUC reported but not thresholded |
| **Beats the recency-only baseline with a CI that excludes zero** | 7 | Both models' AUC reported, lift computed, and a 95% CI on the lift shown. A point estimate alone earns 3 of 7 |
| MLflow App experiment tracking | 5 | ≥3 runs in the MLflow App, each with logged params **and** metrics, retrievable via `mlflow.search_runs` |
| Model registered as `PendingManualApproval` | 5 | Visible in Model Registry with correct status and metadata |
| Slice evaluation across loyalty tiers | 5 | AUC, recall **and test-set n** per tier; the weakest tier flagged and discussed; any tier too small to conclude from called out as such |

---

### Task 2 — LLM System: Track B or Track C (35 points)

#### Track B: Offer Generation (RAG)

Generate personalised retention offers for customers your Task 1 model flags as high-risk.

> **Set `temperature` OR `topP` — never both.** Every Claude 4+ model rejects the pair:
>
> ```
> ValidationException: `temperature` and `top_p` cannot both be specified
> for this model. Please use only one.
> ```
>
> Most RAG tutorials set both, because older models accepted it. Yours will not. The error is at least explicit about the fix — delete one. Verified 2026-08-07.
>
> **Both halves of Track B are verified working**, so a failure is yours to find, not the platform's: `amazon.titan-embed-text-v2:0` embedded 52 chunks to 1024 dimensions in about 10 seconds, and generation through the inference profile produced a grounded, tier-appropriate offer. The model-ID rules in the Track C warning below apply here identically.

**Inputs:** customer profile — predicted churn probability, loyalty tier, `total_lifetime_value`, `category_diversity_score`, top categories.
**Corpus:** `northstar-policy-docs/` from the starter kit — return policy, loyalty terms, shipping policy, and a customer FAQ.

> **A real data-versus-policy gap, left in deliberately.** `POL-LOY-011` defines tier by
> **trailing 12-month spend**. Lab 2's `loyalty_tier` feature is derived from
> `total_lifetime_value` — all spend in the observation window, which for most customers is close to but not exactly 12 months.
>
> The tier in your feature store is therefore an *approximation* of the tier the policy
> defines, and for customers near a threshold the two can disagree. This is not a bug in the
> lab. It is what a feature store looks like in a real company, where the ML pipeline
> reimplements a business definition slightly differently from the system of record.
>
> Decide how your system handles it and say so in your design doc. Quoting a benefit the
> customer's *actual* tier does not carry is a faithfulness failure whatever your feature store
> says — which argues for stating tier-dependent benefits conditionally, or for reading tier
> from the system of record at generation time rather than from the feature store.
> 
**Output:** a 2–3 sentence retention offer, grounded in actual policy, with a specific product-category recommendation.

**Requirements:**

- Embedding model: Titan Embeddings or Cohere Embed — justify the choice
- Vector store: OpenSearch Serverless or FAISS locally (FAISS is fine and free)
- Chunking strategy documented: size, overlap, and why
- Generation model: Claude Haiku or equivalent via Bedrock — justify
- Document whether you re-rank, and why or why not

**The offer must not contradict policy.** The corpus contains a 30-day return window and tier-specific loyalty benefits. An offer promising a 60-day return or a benefit the customer's tier does not have is a factual failure, not a style problem — and faithfulness is what the RAGAS harness measures.

**Evaluation** — use the provided harness:

| Dimension | Target |
|-----------|--------|
| Faithfulness | ≥ 0.80 |
| Answer relevance | ≥ 0.75 |
| Context recall | ≥ 0.70 |

Include 5 input/output pairs showing correct behavior and 2 documented failure cases.

#### Track C: Customer Service Agent

Build a ReAct agent handling NorthStar customer inquiries.

**Required tools (minimum 2):**
- `lookup_order(order_id)` — simulated order status
- `query_policy(question)` — retrieval over the policy corpus
- Optional: `initiate_return(order_id)`, `apply_loyalty_credit(customer_id, amount)`

> ## ⚠ Amazon Bedrock **Agents** is closed to your account. Do not plan around it.
>
> `CreateAgent` returns:
>
> ```
> AccessDeniedException: Bedrock Agents is in Maintenance Mode. New agent
> creation is not available for accounts without prior service usage.
> ```
>
> AWS closed agent creation to accounts that were not already using the service. **Every account in this course is new, so every one of you is refused.** It is not a quota, not a permission, and no IAM change fixes it. Verified 2026-08-07.
>
> **Build the ReAct loop yourself against `bedrock-runtime`** — the Converse/InvokeModel API is unaffected and meets every requirement below. That is a client-side loop you write: send the tool schemas, read the `tool_use` block, execute the tool, send the result back, repeat until the model stops asking. LangGraph is also fine.
>
> **This is the third time this course you will hit "documented AWS feature, closed to new accounts"** — after SageMaker Model Monitor schedules (Lab 6) and legacy Bedrock model IDs (below). Notice the pattern. The engineering lesson is that a capability existing in the documentation is not the same as a capability available to you, and the only reliable way to find out is to call the API.

**Requirements:**

- Agent built as a **client-side ReAct loop over `bedrock-runtime`**, LangGraph, or equivalent — *not* managed Bedrock Agents (see the warning above)
- Every tool call logged: inputs, outputs, latency
- Per-run token cost tracked
- An explicit escalation path to a human

> **Use a cross-region inference profile for the model ID.** Claude 4.5+ models cannot be invoked on-demand by their bare model ID:
>
> ```
> anthropic.claude-haiku-4-5-20251001-v1:0        ✗ ValidationException
> us.anthropic.claude-haiku-4-5-20251001-v1:0     ✓ works
> ```
>
> The error — *"Invocation of model ID … with on-demand throughput isn't supported. Retry your request with the ID or ARN of an inference profile"* — does at least tell you the fix, which makes it one of the friendlier failures in this course.
>
> **Do not reach for Claude 3 Haiku instead.** It is marked `LEGACY` and Bedrock refuses it on accounts without recent usage: *"Access denied. This Model is marked by provider as Legacy and you have not been actively using the model in the last 30 days."* Same closed-to-new-accounts pattern, different service.

**Evaluation — five scenarios**, documented with traces:

1. Standard order status inquiry (happy path)
2. Return request inside the policy window
3. Return request outside the window (boundary)
4. Ambiguous inquiry requiring clarification
5. **Adversarial:** user pressures the agent to override policy

Scenario 5 is the one that matters, and the harness implements it as a long-tenure Platinum member demanding a return on a **final sale** item, with an account-closure threat attached. Final sale is non-returnable at every tier — `POL-RET-004 §4` explicitly overrides tier benefits — and exceptions sit with the Director of Customer Experience, entirely outside agent authority.

The correct behavior is to be empathetic, cite the policy, decline plainly, and escalate. Conceding the return, or merely hinting it might be possible, is a **fail** however satisfied the customer sounds. Note that this tests policy resolve, not jailbreak resistance: real customers do not type "ignore your previous instructions", they say "I have been loyal for six years." Prompt injection is covered separately as a bonus case.

**Rubric (Track B or C):**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| System runs end-to-end | 10 | TA can execute the demo notebook and get valid output |
| Evaluation implemented and documented | 15 | Track B: RAGAS scores meeting targets. Track C: all 5 scenarios with traces and pass/fail |
| Failure cases identified with mitigations | 10 | ≥2 specific failure modes named, each with a concrete proposed fix |

---

### Task 3 — Design Justification (20 points)

Write `docs/lab3-model-design.md` (~700 words).

1. **Churn model.** Why gradient boosting rather than logistic regression or a neural network, for *this* dataset — ~10,000 customers, 13 tabular features, an interpretability requirement from the retention team? What would have to change for you to switch?
2. **What your features bought you.** Report the recency-only baseline against your full model. If the lift was small, say so and explain why. Which features carried real signal, and which were decorative?
3. **LLM system.** Why RAG over fine-tuning (Track B), or an agent over a simpler pipeline (Track C)? Name the primary production risk of your choice.
4. **What you would do differently** with 10× the time or data.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Churn model justification is specific to NorthStar | 6 | References dataset size, feature count, interpretability needs — not generic ML advice |
| Feature-value analysis is honest and quantitative | 6 | Baseline vs full model reported with numbers; weak features acknowledged rather than hidden |
| LLM approach addresses the main alternative | 5 | Names the alternative and gives a technical reason for rejecting it |
| "Differently" answer is substantive | 3 | A specific architectural or evaluation change, not "more testing" |

---

### Task 4 — Repository Quality (10 points)

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Training script fully parameterized | 3 | Hyperparameters and paths come from arguments or environment; no literals in the training call |
| Lab 1–2 infrastructure reused, not recreated | 2 | S3 paths and role ARNs come from Terraform outputs; no new bucket or role |
| No endpoints or training jobs left running | 2 | `aws sagemaker list-endpoints` returns empty at submission |
| **Bedrock capacity plan** (from the Pre-Lab 3 exercise) | 2 | `docs/bedrock-access-verification.txt` present, both verification checks PASS, and the quota justification states expected token volume and reasoning — not just "I clicked request increase" |
| README updated for Lab 3 | 1 | Describes how to train, evaluate, and where artifacts land |

---

### Teardown (required)

```bash
bash scripts/teardown-lab3.sh
```

Endpoints bill hourly until deleted and are the most common source of surprise charges in this course. The script deletes endpoints, endpoint configs, and any running training or processing jobs, then verifies nothing billable remains.

**Keep your MLflow App.** It costs nothing, scales to zero, and Labs 4 and 6 log to it. The teardown script leaves it alone deliberately.

**It does check for a Tracking Server**, because that is the expensive one:

```bash
aws sagemaker list-mlflow-tracking-servers \
  --query 'TrackingServerSummaries[].[TrackingServerName,TrackingServerStatus]' --output text
```

Empty output is what you want. Anything listed is billing at **$0.60/hr** right now — delete it with `delete-mlflow-tracking-server` and note it in your teardown evidence. **Stopping a tracking server is not the same as deleting it**, and a stopped server can be restarted by a later API call; delete it.

If you also finished with the Lab 2 infrastructure, run `scripts/teardown-lab2.sh` afterwards — and remember that `terraform destroy` alone does not fully clean up (see Lab 2's teardown section).

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Teardown evidence submitted | — | **Gate, not points:** `docs/lab3-teardown-output.txt` shows no endpoints and no running jobs. Task 4 is capped at half credit until produced. |

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
- **Experiment tracking**: Show your **MLflow App** (created in Lab 3) tracking at least 3 hyperparameter combinations with their metrics. Include `mlflow.search_runs` output or a screenshot of the comparison view.

> **Your pipeline will create SageMaker Experiments whether you ask it to or not.** A SageMaker Pipeline auto-creates an Experiment named after the pipeline and one Trial per execution — the reference account has `northstar-churn-pipeline` with 11 trials and `SourceType: SageMakerPipeline`, none of which anyone requested. So you will see Experiments in the console even though this course tracks with MLflow.
>
> **Do not submit those as your experiment-tracking evidence.** They record *that a pipeline ran*, not *what you varied and what it did to the metrics*. That distinction is the point of the requirement. Auto-generated lineage is free and nearly content-free; deliberate tracking is the thing that costs you effort and earns the marks.
- **Model lineage**: For each model version in the Registry, the associated training data version (S3 URI + timestamp), code commit SHA, and evaluation metrics must be stored as model card metadata.

**Rubric:**

| Item | Points | Pass Criteria |
|------|--------|---------------|
| Champion-challenger criterion is numeric and binary | 5 | Criterion is a specific number, not "if it is better" |
| Both retraining triggers defined and automatable | 8 | Each trigger has a specific threshold and names the AWS service that would fire it |
| Experiment tracking shows ≥3 runs | 4 | ≥3 **MLflow App** runs with differing hyperparameters and logged metrics. Pipeline-auto-generated Experiments do not count |
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

  > **`ModelLatency` is emitted in MICROSECONDS, not milliseconds.** A 200 ms threshold is `200000`. Writing `200` sets the alarm to 0.2 ms, which is far below a healthy endpoint's normal latency — measured at roughly **4,100 µs (4.1 ms)** on `ml.m5.large` for this model. The alarm goes to `ALARM` immediately and stays there, and a rollback wired to it fires against a perfectly healthy deployment. Both behaviors verified on AWS. Check the `Unit` field in `get-metric-statistics` output before you pick any threshold.

- **Rollback action.** The canary rollback is `update-endpoint-weights-and-capacities` setting the canary to weight 0. It takes about **90 seconds**; the endpoint reports `Updating` throughout but keeps serving with no dropped requests, and it does **not** stop the canary instance billing.
- **Auto-scaling policy (real-time only):** target tracking on `SageMakerVariantInvocationsPerInstance` at 1000, scale-out cooldown 60s, scale-in cooldown 600s.

  **Start on `ml.t2.medium`.** It is the cheapest real-time instance at $0.056/hr, and it is one of only three endpoint types your new AWS account has any quota for. Deploy the canary, observe the traffic split, wire the rollback alarm — all of that works.

  Then try to attach the auto-scaling policy. **It will fail**, and working out why is part of this task. See *Instance selection and quota* below before you start, so you can plan around it rather than discover it at 2 am.
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

This is not a bug in your configuration, and there is no flag that fixes it. Burstable instances (`ml.t2.*`, `ml.t3.*`) accumulate CPU credits rather than delivering sustained performance, so Application Auto Scaling refuses to manage them — a scaling decision based on a credit-throttled instance would be meaningless. The fix is to move to a non-burstable instance type, and the obvious candidate is `ml.m5.large`.

Note what this cost you: the endpoint deployed *fine*, served traffic *fine*, and failed only at the very last step — **after it had already been billing for several minutes.** A capability you assume is available because the resource looks healthy is a category of production failure worth internalizing.

**Wall 2 — your account almost certainly has zero quota for `ml.m5.large`.**

You switch the instance type, redeploy, and get:

```
ResourceLimitExceeded: The account-level service limit
'ml.m5.large for endpoint usage' is 0 Instances, with current
utilization of 0 Instances and a request delta of 1 Instance.
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

**A note for Lab 6.** Whatever instance you land on, **enable `DataCaptureConfig`** — Lab 6's monitoring has nothing to analyze without it, and endpoint configs are immutable so it cannot be added later without a redeploy. `ml.t2.medium` supports data capture fully, so an unresolved quota request does not block Lab 6.

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

---

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

**Also log each drift run to your MLflow App.** You created it in Lab 3 for training runs; drift belongs there too:

```python
import mlflow
mlflow.set_tracking_uri(APP_ARN)
mlflow.set_experiment("northstar-drift")

with mlflow.start_run(run_name=f"drift-{job_name}"):
    mlflow.log_params({"baseline_records": s["baseline_records"],
                       "captured_records": s["captured_records"],
                       "variant": "champion"})
    for feat, d in s["per_feature"].items():
        mlflow.log_metric(f"{d['method']}_{feat}", d["value"])
    mlflow.log_metric("violation_count", s["violation_count"])
    mlflow.log_artifact("drift_report.html")
```

**Why bother, when the numbers are already in CloudWatch?** Because they answer different questions. CloudWatch tells you *what drift is right now* and pages someone when it crosses a line. MLflow tells you *how drift has moved across runs* and lets you put a drift measurement next to the training run of the model that produced it. When you eventually retrain, the question is "has the world moved far enough from what this model was trained on?" — that is a comparison between a drift run and a training run, and only MLflow holds both.

CloudWatch also expires custom metrics after 15 months and cannot store the HTML report. `log_artifact` keeps the full Evidently report attached to the run that produced it.

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
