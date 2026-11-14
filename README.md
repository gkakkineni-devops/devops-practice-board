# devops-practice-board

[![ci](https://github.com/gkakkineni-devops/devops-practice-board/actions/workflows/ci.yml/badge.svg)](https://github.com/gkakkineni-devops/devops-practice-board/actions/workflows/ci.yml)

A backlog of DevOps problems that I work through, one small tested project at a time.

The tickets are written as if they came from the platform team of a made-up online shop. The shop is invented and so are the requests. The problems are the kind real teams have, and the code, tests and pipelines behind the finished ones are real. Nothing here comes from a job.

My portfolio shows this backlog as a live board: [gkakkineni-devops.github.io/practice](https://gkakkineni-devops.github.io/practice/).

## The board

<!-- board:start -->
| # | Problem | Status | Area | Where |
|---|---|---|---|---|
| 001 | [A bad release reaches every user](problems/001-bad-release-reaches-everyone.md) | Done | Delivery | [gitops-canary-rollouts](https://github.com/gkakkineni-devops/gitops-canary-rollouts) |
| 002 | [Alerts nobody trusts](problems/002-alerts-nobody-trusts.md) | Done | Observability | [observability-stack](https://github.com/gkakkineni-devops/observability-stack) |
| 003 | [GPU nodes burn money while idle](problems/003-gpu-nodes-burn-money.md) | Done | Cost | [terraform-aws-eks-gpu](https://github.com/gkakkineni-devops/terraform-aws-eks-gpu) |
| 004 | [Nobody knows what is wasting money in AWS](problems/004-idle-aws-resources.md) | Done | Cost | [aws-idle-resource-finder](https://github.com/gkakkineni-devops/aws-idle-resource-finder) |
| 005 | [Secrets end up in commits](problems/005-secrets-in-commits.md) | Open | Security |  |
| 006 | [Terraform drifts from reality](problems/006-terraform-drift.md) | Open | Infrastructure |  |
| 007 | [The pipeline takes too long](problems/007-slow-pipeline.md) | Open | Delivery |  |
<!-- board:end -->

## How a ticket works

Each ticket is a Markdown file in `problems/`. The top of the file holds a few fields: status, area, tools and the repo that holds the work. The rest is written in the same order every time.

- **Open tickets** say what "done" means before any work starts: the ask, why it hurts, and a short list under "Done when".
- **Finished tickets** say what I built, how I know it works, what went wrong on the way, and what it still doesn't do.

I only mark a ticket done when its repo has a passing pipeline and I can say what isn't covered. If a project was never run against real infrastructure, the write-up says so.

## Add a ticket

1. Copy `problems/_template.md` to `problems/NNN-short-name.md` and fill it in.
2. Run `python scripts/build_board.py`. It checks the ticket and rewrites `board.json` and the table above.
3. Commit all three files.

CI runs the same script with `--check`, so a ticket that is missing a section, or a board that wasn't regenerated, fails the build.

## What the script does

`scripts/build_board.py` reads every ticket, checks the fields and the headings, and writes `board.json`. It uses only the standard library. The tests are in `tests/` and run with `python -m unittest`.

`board.json` is what my portfolio reads. The site's build fetches it every few hours, so the board there follows this repo without anyone editing the site.

## License

MIT
