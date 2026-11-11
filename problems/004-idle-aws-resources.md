---
id: 004
title: Nobody knows what is wasting money in AWS
status: open
area: Cost
repo:
site_page:
post:
tools: Python, AWS Lambda, Terraform, EventBridge, boto3, pytest, GitHub Actions
summary: A weekly report of idle AWS resources and what they cost. It only reads and never deletes.
---

## The ask

The AWS bill goes up every month and nobody can say which resources are doing nothing. Can we get a list every week of what looks idle, with a rough cost next to each item?

## Why it hurts

Disks that no longer have a server, public IPs that point at nothing and snapshots from last year keep billing quietly. They tend to be found by accident, usually when someone is already looking at the bill. A machine with no owner tag is worse, because nobody knows who to ask before switching it off.

## Done when

- A Lambda function finds unattached EBS volumes, unassociated Elastic IPs, old snapshots and EC2 instances that are missing an owner or project tag.
- The rules are plain functions with tests, so they run without an AWS account.
- Every finding has an estimated monthly cost, and the README says the prices are estimates.
- The IAM role can only read EC2 and write to one folder of one S3 bucket. Nothing can delete or change a resource.
- Terraform deploys the function, the bucket, the logs and a weekly schedule, and CI checks the Terraform.
- I have run it once in a real AWS account and destroyed it afterwards, or the README says that I haven't.
