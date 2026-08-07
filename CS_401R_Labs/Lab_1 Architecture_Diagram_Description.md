### **Requirements:**
- Official AWS icons (Cloudcraft, draw.io, or aws.amazon.com/architecture/icons)
- Show VPC boundary containing the public subnet in `us-east-1a`
- Show all resources with their exact names
- Show MLEngineer role with arrows to the S3 prefixes it accesses
- Show Internet Gateway connecting the public subnet to the internet
- Legend identifying each icon type

#### Boundary: AWS Region `us-east-1`

##### Boundary: VPC — `northstar-dev-vpc`
- **CIDR:** `10.0.0.0/16`
- **DNS hostnames:** enabled
- **DNS resolution:** enabled

###### Boundary: Availability Zone `us-east-1a`

**Public Subnet — `northstar-dev-public-1`**
- CIDR: `10.0.100.0/24`
- Public IP on launch: yes
- Contains: SageMaker Studio, Internet Gateway route

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

