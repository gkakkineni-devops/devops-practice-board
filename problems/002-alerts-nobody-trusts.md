---
id: 002
title: Alerts nobody trusts
status: done
area: Observability
repo: observability-stack
site_page: work/observability-stack/
tools: Prometheus, Alertmanager, Grafana, Docker Compose, promtool, Python
summary: Alert rules with unit tests, and a check that a real failure really pages.
---

## The ask

We got paged for nothing twice last month, and once an outage went by without any page at all. Can we trust our alerts, and can we find out a rule is broken before the outage does?

## Why it hurts

Monitoring usually gets built by clicking around, and nobody tests it. The first time anyone learns a rule has a typo is during an outage, when nobody gets paged. After a few false alarms people also stop reading the pages that are real.

## What I built

- Prometheus scraping a small demo service, node-exporter and Alertmanager every five seconds, with recording rules that work out request rate, error ratio and p95 latency once. The dashboard and the alerts then use the same numbers.
- Six alert rules: instance down, fast error-budget burn, high error ratio, high p95 latency, a disk that will fill within four hours, and memory above 90% for ten minutes. Each one has a summary and a runbook line.
- An error-budget burn alert for a 99.9% target. It fires when errors are using the budget 14.4 times too fast over both the last 5 minutes and the last hour, so a short blip doesn't page anyone but a real outage still does.
- Alertmanager grouping alerts by name and job, repeating critical ones every 30 minutes, and muting warnings for a job that already has a critical alert firing.
- A Grafana dashboard provisioned from files, so it lives in Git and comes back identical after a rebuild.

## How I know it works

The alert rules have unit tests. `promtool` feeds fake time series into the rules and checks which alerts fire and what they say. CI also checks the Prometheus and Alertmanager configs and validates the dashboard JSON, lints the Dockerfile with hadolint and scans with Trivy. Then it starts the whole stack, breaks the demo service on purpose, keeps sending traffic, waits for the alert to fire in Prometheus and checks that it reached Alertmanager.

## What went wrong on the way

- My first smoke test only checked that the error ratio went up. That proves a metric moved, not that anyone would be paged, so I changed it to check the alert itself.
- The test has to keep sending traffic. Without new requests the rate goes flat and the alert clears itself before the check looks.
- My first test file sat in the rules folder. Prometheus loads everything there as rules, so it refused to start. The tests now have their own folder.

## What it doesn't do yet

- The webhook receiver only prints alerts. A real setup would send them to Slack or a pager.
- The thresholds are tuned for a demo service, not for real traffic.
- It runs on one node with no persistent storage, and Grafana keeps its default login. Every port is bound to localhost for that reason.
