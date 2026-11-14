---
id: 004
title: Nobody knows what is wasting money in AWS
status: done
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

- Four rules written as plain functions with no AWS inside: unattached EBS volumes, unassociated Elastic IPs, snapshots older than 90 days and instances missing an owner or project tag. Each one takes the data boto3 returns and gives back findings with an estimated monthly cost. The snapshot rule takes the current time as an argument, so a test can pick any date.
- A report with the estimated monthly total, a count per kind and the findings sorted most expensive first.
- One file that talks to AWS. Every function takes the client as an argument, so the tests pass in a fake one. Settings come from environment variables, the way Lambda is configured.
- A Lambda handler, and a command line entry point that runs the same scan from a laptop and only prints.
- Terraform for the function, an IAM role that can read four kinds of EC2 resources and write to one folder of one bucket, a private encrypted S3 bucket that expires old reports, a log group with a retention period, and a weekly EventBridge schedule. Nothing in the role can delete or change a resource.
- CI with Dependabot, built over eight small pull requests, one issue each.

## How I know it works

Partly. Every push runs ruff and 27 unit tests, one of which runs the real boto3 calls against moto, a pretend AWS. A second CI job runs a Trivy scan of the Terraform, `terraform fmt`, `init` and `validate` against the real AWS provider, and tflint. All of that is green. What I have not done is run it against a real AWS account, so I haven't seen a real report from a real account. The README says so and leaves those three boxes unticked.

## What went wrong on the way

Nothing failed in CI. Every job was green the first time it ran, including the Terraform checks and the moto test, which I had never run before. That means this ticket has no breakage to report. The first thing I'd expect to go wrong on a real deploy is a permission or a setting that only a live account shows up.

## What it doesn't do yet

- It has never run on a real AWS account. A real run, with a billing alarm set first and everything destroyed afterwards, is still to do.
- It only reports. Cleaning up would need a dry run mode, an opt-in tag and a way to undo it.
- One region per deployment, and it doesn't look at CPU use, so an instance that is attached but idle isn't found.
- The prices are typed-in constants for us-east-1, with one flat price for every volume type.
- Terraform state is local. A team would keep it in S3 with locking.
