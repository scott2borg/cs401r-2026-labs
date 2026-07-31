# CS 401R — Building the NorthStar Retail AI Platform

Lab specifications and starter kits for **CS 401R, Brigham Young University, Fall 2026**.

Across seven labs you build a production AI platform on AWS: infrastructure, a data and feature pipeline, a churn model, CI/CD, a controlled deployment, full monitoring, and a business-value analysis.

## What's here

| Path | Contents |
|---|---|
| `CS_401R_Labs/CS 401R Labs.md` | The complete lab guide — all labs in one document |
| `CS_401R_Labs/Lab_N--*.md` | Individual lab specifications |
| `CS_401R_Labs/Starter Kits/Lab N/` | Starter code and data for each lab |
| `CS_401R_Labs/Fix Credentials Problem.md` | AWS credential troubleshooting |
| `CS_401R_Labs/Pre-Lab 3 — Bedrock Access Setup.md` | Bedrock model access — **start this early** |

Starter kits are also distributed through Canvas. This repository is the canonical copy.

## Before you start

**You need your own AWS account.** It is independent of BYU — BYU does not administer it, cannot see it, and cannot pay for it. You are responsible for everything you create in it.

**Set a billing alarm on day one.** Several labs create resources that bill *by the hour until you delete them*. A SageMaker endpoint does not idle down, does not expire, and nothing will remind you it is running. A forgotten endpoint can cost more than every other resource in the course combined.

**Every lab has a teardown section. Teardown is a gate, not a suggestion.** Resources still running after a deadline are penalised on top of the gate.

**Two labs have lead times you cannot compress:**

- **Lab 3** needs Amazon Bedrock model access — request it as soon as Pre-Lab 3 is assigned.
- **Lab 5** needs a SageMaker service quota increase. New AWS accounts ship with a quota of **zero** for most on-demand instance types. Approval has ranged from minutes to several business days. **File the request the day Lab 5 is assigned.** The lab is designed so you can do the first half while it is pending.

Neither is a mistake you made. Both are real platform constraints, and working through them is part of the course.

## Cost expectations

Every lab is designed to run inside AWS default service quotas and to cost well under a dollar if you follow the teardown steps. The reference runs that produced the timings in these specs cost **under $0.20** per lab.

The cost risk is not any single resource — it is forgetting one. Read the "Read This First — Cost" section in Labs 5 and 6 before you deploy anything.

## Getting help

Bring the **CLI output**, not a screenshot. The AWS console's resource views lag by hours and have shown deleted resources as still present in this course before. `aws ... describe-*` output is authoritative.

---

*Solutions and grading materials are maintained separately and are not published here.*
