---
id: 001
title: A bad release reaches every user
status: done
area: Delivery
repo: gitops-canary-rollouts
site_page: work/gitops-canary-rollouts/
tools: Helm, Argo Rollouts, Argo CD, kind, GitHub Actions
summary: Release a new version in steps, and stop it on its own if it breaks.
---

## The ask

Every release goes to all users at once. When one is bad, everyone sees it before we do. Can releases go out in steps, and stop themselves when something is wrong?

## Why it hurts

A release to everyone is a bet. If it's bad, every user hits the problem together, and getting back depends on someone noticing, deciding and acting, usually in a hurry.

## What I built

- A Helm chart that uses an Argo Rollouts `Rollout` instead of a `Deployment`: 20% of the pods first, a pause, then 60%, another pause, then everyone.
- A check that runs during each pause. A small Kubernetes Job sends 10 requests to the canary Service and expects a 200 every time. It runs three times, 10 seconds apart, and a second failed run aborts the release.
- A progress deadline of 90 seconds with abort turned on, so pods that never become ready are rolled back.
- Two Services, one stable and one canary, so the check only tests the new version.
- An Argo CD Application with auto-sync, prune and self-heal, so the cluster follows what is in Git.

## How I know it works

CI starts a throwaway kind cluster, installs Argo Rollouts and runs a release test. It ships a good release and checks it finishes healthy on the new version. Then it ships an image tag that doesn't exist and checks the rollout fails. The last check is the important one: the stable Service still answers with a 200 and the pods are still on the last good version. The same pipeline also runs `helm lint --strict`, kubeconform and a Trivy config scan.

## What went wrong on the way

- My first Trivy step used an action version that didn't exist. I switched to running Trivy from its Docker image, which pins the version and behaves the same on my laptop.
- Helm and Argo both use double curly braces. Helm tried to fill in Argo's canary Service variable and broke the check, so the chart now escapes it.
- A pod stuck pulling a missing image held a release for ten minutes before Kubernetes gave up. The 90 second progress deadline fixed that.
- When I moved to a newer Argo Rollouts, the install went red until I applied it with `kubectl apply --server-side`.

## What it doesn't do yet

- Traffic is split by pod count, not by a traffic router. With five pods, 20% is one pod.
- The check only looks for a 200. A real service should judge the canary on error rate and latency from metrics.
- The Argo CD Application hasn't run against a live Argo CD. CI covers the chart and the release behaviour on kind, not a cloud cluster.
