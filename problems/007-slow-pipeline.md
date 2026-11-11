---
id: 007
title: The pipeline takes too long
status: open
area: Delivery
repo:
site_page:
post:
tools: GitHub Actions, Docker, Caching
summary: Measure a slow pipeline, speed it up, and report the real before and after.
---

## The ask

Developers wait around 20 minutes for a pull request to go green, so they stop waiting and start something else. Can we make the pipeline faster, and show by how much?

## Why it hurts

A slow pipeline makes every change more expensive. People batch up their work into bigger pull requests, which are harder to review, and a failure found after 20 minutes costs more than one found after five.

## Done when

- The baseline run time comes from real workflow runs, not from a guess.
- Dependency and Docker layer caching are added, and parallel jobs where the steps don't depend on each other.
- The write-up shows before and after times from real runs.
- It also lists what I tried that didn't help.
