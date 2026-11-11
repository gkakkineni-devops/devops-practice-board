---
id: 006
title: Terraform drifts from reality
status: open
area: Infrastructure
repo:
site_page:
post:
tools: Terraform, Docker, GitHub Actions
summary: A scheduled plan that notices when someone changes things by hand.
---

## The ask

Someone changed a setting in the console during an incident and never wrote it back to the code. Now the next apply would quietly undo it. Can we find out when reality and the code stop matching?

## Why it hurts

Terraform only knows what it last applied. A change made by hand stays invisible until the next apply, which then reverts it, sometimes in the middle of another incident.

## Done when

- Terraform manages something small that runs locally, so the whole project costs nothing.
- A scheduled workflow runs `terraform plan -detailed-exitcode` and opens a GitHub issue with the plan output when it finds a difference.
- CI proves the detection: it changes the resource by hand on purpose and checks that the workflow notices.
- The write-up explains the two ways to fix drift, apply the code or import the change, and when to pick which.
