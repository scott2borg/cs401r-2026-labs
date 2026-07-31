```bash
cd northstar-ai-platform
docker compose up -d && docker compose ps

awslocal sts get-caller-identity
awslocal s3 ls s3://northstar-local-data-000000000000/ --recursive
awslocal iam list-roles --query 'Roles[?starts_with(RoleName, `northstar`)].RoleName'
awslocal ec2 describe-vpcs --query 'Vpcs[*].{Id:VpcId,CIDR:CidrBlock}'
awslocal ec2 describe-subnets --query 'Subnets[*].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}'
```

This set of commands is a common verification sequence when working with **LocalStack**, a local AWS cloud emulator. The idea is to (1) start the local AWS environment, and then (2) verify that the expected AWS resources exist.

---

# **1. Start LocalStack**

```bash
docker compose up -d && docker compose ps
```

These are **two commands** connected with `&&`.

### **First command**

```bash
docker compose up -d
```

**Purpose:**

Starts all containers defined in your `docker-compose.yml`.

Example:

```
docker-compose.yml
```

might contain

- LocalStack
- PostgreSQL
- Redis
- MLflow
- etc.

The `up` command

- creates containers if necessary
- starts them
- creates Docker networks
- mounts volumes


### **The** **`-d`** **option**

```
-d
```

means

Detached mode

Instead of occupying your terminal, Docker runs in the background.

Without `-d`

```
docker compose up
```

your terminal would continually display container logs.

---

### **Second command**

```bash
docker compose ps
```

Shows the status of the containers.

Example output

```
NAME             STATUS          PORTS
localstack       running         4566->4566
postgres         running         5432->5432
redis            running         6379->6379
```

This lets you quickly verify everything started successfully.

---

### **Why use** **`&&`** **?**

```
command1 && command2
```

means

Execute command2 **only if** command1 succeeds.

So

```
docker compose up -d && docker compose ps
```

means

1. Start everything.
2. If successful, display container status.

---

# **2. Verify your AWS identity**

```bash
awslocal sts get-caller-identity
```

Normally you would run

```bash
aws sts get-caller-identity
```

against the real AWS cloud.

Here you’re using

```
awslocal
```

which is a convenience wrapper that automatically points the AWS CLI at your LocalStack endpoint (typically `http://localhost:4566`).

---

### **STS**

STS = **Security Token Service**

The command

```bash
get-caller-identity
```

asks

“Who am I authenticated as?”

Example response

```json
{
  "UserId": "AKIAIOSFODNN7",
  "Account": "000000000000",
  "Arn": "arn:aws:iam::000000000000:user/local"
}
```

Notice the account number

```
000000000000
```

That’s LocalStack’s default account ID—not a real AWS account.

This verifies:

- LocalStack is responding.
- The AWS CLI can connect to it.
- Credentials are working (LocalStack accepts any credentials by default).

---

# **3. List the contents of an S3 bucket**

```bash
awslocal s3 ls s3://northstar-local-data-000000000000/ --recursive
```

Let’s break it down.

### **`s3 ls`**

```
ls
```

means “list.”

Equivalent to

```
ls
```

on Linux, but for S3 objects.

---

### **Bucket**

```
s3://northstar-local-data-000000000000/
```

Bucket name:

```
northstar-local-data-000000000000
```

This bucket likely stores:

- CSV files
- Parquet data
- training datasets
- model artifacts

---

### **`--recursive`**

Without it:

```
folder1/
folder2/
```

With it:

```
folder1/data.csv
folder1/train.parquet
folder2/model.pkl
```

It traverses the entire bucket.

---

Example output

```
2026-07-30 10:15:22      15234 raw/customers.csv
2026-07-30 10:15:30     923421 features/train.parquet
2026-07-30 10:15:42      51244 models/model.tar.gz
```

---

# **4. List IAM roles**

```bash
awslocal iam list-roles \
  --query 'Roles[?starts_with(RoleName, `northstar`)].RoleName'
```

This command retrieves all IAM roles and then filters them using a **JMESPath** query.

---

### **Step 1**

```
list-roles
```

Returns JSON like

```json
{
  "Roles":[
      {
         "RoleName":"northstar-sagemaker-role"
      },
      {
         "RoleName":"northstar-glue-role"
      },
      {
         "RoleName":"AWSServiceRoleForSupport"
      }
  ]
}
```

---

### **Step 2**

The query

```text
Roles[?starts_with(RoleName, `northstar`)].RoleName
```

means

```
Roles
```

Look inside the Roles array.

```
[? ... ]
```

Filter the array.

```
starts_with(RoleName, `northstar`)
```

Keep only roles whose name begins with

```
northstar
```

Finally

```
.RoleName
```

Return only the names.

Result

```text
[
    "northstar-sagemaker-role",
    "northstar-glue-role",
    "northstar-lambda-role"
]
```

---

# **5. Show VPCs**

```bash
awslocal ec2 describe-vpcs \
  --query 'Vpcs[*].{Id:VpcId,CIDR:CidrBlock}'
```

Without the query, the output is very large:

```json
{
   "Vpcs":[
      {
         "VpcId":"vpc-12345",
         "CidrBlock":"10.0.0.0/16",
         ...
      }
   ]
}
```

The query

```text
Vpcs[*]
```

means

Every VPC.

For each VPC,

```text
{
   Id:VpcId,
   CIDR:CidrBlock
}
```

create a simplified object.

Output

```json
[
  {
    "Id": "vpc-12345",
    "CIDR": "10.0.0.0/16"
  }
]
```

This is much easier to read.

---

# **6. Show subnets**

```bash
awslocal ec2 describe-subnets \
  --query 'Subnets[*].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock}'
```

This works the same way.

Each subnet is transformed into a concise object containing:

- subnet ID
- availability zone
- CIDR block

Example

```json
[
  {
    "Id": "subnet-1111",
    "AZ": "us-east-1a",
    "CIDR": "10.0.1.0/24"
  },
  {
    "Id": "subnet-2222",
    "AZ": "us-east-1b",
    "CIDR": "10.0.2.0/24"
  }
]
```

---

# **Putting it all together**

These commands form a quick “sanity check” for a LocalStack-based AWS development environment:

|**Command**|**Purpose**|**What it verifies**|
|---|---|---|
|`docker compose up -d`|Start the local infrastructure|Containers launch successfully|
|`docker compose ps`|Display container status|Required services are running|
|`awslocal sts get-caller-identity`|Check AWS identity|LocalStack is reachable and AWS CLI is configured|
|`awslocal s3 ls ... --recursive`|List bucket contents|The expected S3 bucket exists and contains data|
|`awslocal iam list-roles ...`|List project IAM roles|IAM resources have been provisioned|
|`awslocal ec2 describe-vpcs ...`|Show VPCs|Networking infrastructure exists|
|`awslocal ec2 describe-subnets ...`|Show subnets|The VPC contains the expected subnets|

Taken together, this sequence confirms that your local AWS environment is up, accessible, and provisioned with the key resources (identity, storage, permissions, and networking) needed before you begin developing or testing applications.