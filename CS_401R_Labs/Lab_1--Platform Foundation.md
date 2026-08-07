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
  - SageMaker: training jobs, endpoints, experiments, model registry
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
        "sagemaker:CreateExperiment", "sagemaker:DescribeExperiment",
        "sagemaker:CreateTrial", "sagemaker:DescribeTrial",
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
