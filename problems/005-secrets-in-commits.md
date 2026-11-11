---
id: 005
title: Secrets end up in commits
status: open
area: Security
repo:
site_page:
post:
tools: gitleaks, pre-commit, GitHub Actions, Python
summary: Catch a leaked key before it reaches main, and know what to do when one gets through.
---

## The ask

Someone pasted a token into a config file last month and it sat in the repo for two weeks before anyone saw it. Can we catch that before it is merged?

## Why it hurts

A secret in Git history stays there after the file is fixed. Anyone who can read the repo, now or later, can use it, so every leak ends in a rotation, and the longer it sits the more it costs to clean up.

## Done when

- A secret scanner runs on every pull request and blocks the merge when it finds something.
- The same scan runs on my machine as a pre-commit hook, so most leaks never leave the laptop.
- A test shows that a fake key is caught and a harmless file passes.
- The README says what to do when a real key leaks: revoke it first, clean up second.
- The write-up shows what the scanner flagged by mistake and how I handled the false alarms.
