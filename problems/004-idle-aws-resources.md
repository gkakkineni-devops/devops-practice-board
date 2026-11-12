---
id: 004
title: Nobody knows what is wasting money in AWS
status: building
area: Cost
repo: aws-idle-resource-finder
site_page:
post:
tools: Python, AWS Lambda, Terraform, EventBridge, boto3, pytest, GitHub Actions
summary: A weekly report of idle AWS resources and what they cost. It only reads and never deletes.
---

## The ask

The AWS bill goes up every month and nobody can say which resources are doing nothing. Can we get a list every week of what looks idle, with a rough cost next to each item?

## Why it hurts

Disks that no longer have a server, public IPs that point at nothing and snapshots from last year keep billing quietly. They tend to be found by accident, usually when someone is already looking at the bill. A machine with no owner tag is worse, because nobody knows who to ask before switching it off.

## What I built

So far, the first four of eight pull requests are merged:

- The four rules as plain functions with no AWS inside: unattached EBS volumes, unassociated Elastic IPs, snapshots older than 90 days and instances missing an owner or project tag. Each one takes the data boto3 returns and gives back findings with an estimated monthly cost.
- The JSON report: the estimated total, a count per kind, and the findings with the most expensive first.
- The one file that talks to AWS. Every function takes the client as an argument, so the tests hand in a fake one. Settings come from environment variables, the way Lambda is configured.
- The Lambda handler, and a command line entry point that runs the same scan from a laptop and only prints.

Still to come: CI, the Terraform, Terraform checks and Dependabot, and the README.

## How I know it works

Only on my laptop so far. 26 unit tests pass and ruff is clean, and I checked that breaking the snapshot age rule on purpose makes a test fail. One more test runs the real boto3 calls against moto, a pretend AWS, and it has not been run yet. There is no CI yet, so the board shows no pipeline result for this one, and nothing has run on a real AWS account.

## What went wrong on the way

Nothing has broken yet. The Terraform and the security scan have never run, so I expect something there, and I'll write down what happens.

## What it doesn't do yet

- It isn't deployed anywhere yet. The Terraform, CI and README are still to come.
- It will only ever read. Cleaning up would need a dry run mode and a way to undo it.
- One region per run, and the prices are typed in as rough us-east-1 numbers.

## Done when


- A Lambda function finds unattached EBS volumes, unassociated Elastic IPs, old snapshots and EC2 instances that are missing an owner or project tag.
- The rules are plain functions with tests, so they run without an AWS account.
- Every finding has an estimated monthly cost, and the README says the prices are estimates.
- The IAM role can only read EC2 and write to one folder of one S3 bucket. Nothing can delete or change a resource.
- Terraform deploys the function, the bucket, the logs and a weekly schedule, and CI checks the Terraform.
- I have run it once in a real AWS account and destroyed it afterwards, or the README says that I haven't.
