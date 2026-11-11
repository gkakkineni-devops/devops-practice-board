---
id: 003
title: GPU nodes burn money while idle
status: done
area: Cost
repo: terraform-aws-eks-gpu
site_page: work/terraform-aws-eks-gpu/
tools: Terraform, AWS EKS, VPC, Spot instances, tflint, Trivy
summary: A GPU node group that sits at zero nodes until a job needs one.
---

## The ask

The ML team needs GPU nodes now and then, and last quarter a few were left running over a long weekend. Can the platform keep GPUs off unless a job is actually running?

## Why it hurts

GPUs are the most expensive part of an ML platform. A node that nobody scaled down costs real money every hour, and nobody notices until the bill arrives.

## What I built

- A VPC across two availability zones, with private and public subnets and one NAT gateway, using the community VPC module.
- An EKS cluster whose API endpoint is public but limited to the IP addresses you list. The variable has no default and refuses `0.0.0.0/0`, so the API can't be opened to the world by accident.
- A small always-on system node group, so CoreDNS and the controllers have somewhere to run.
- A GPU node group on the NVIDIA EKS image, with a minimum and desired size of zero. It defaults to Spot, switches to on-demand with one variable, and carries a taint so ordinary pods can't land on it.
- A hardened test pod that runs `nvidia-smi` to prove a GPU works.

## How I know it works

Partly. Every push runs `terraform fmt -check`, `terraform init` and `validate`, tflint, a Trivy config scan and kubeconform on the test pod, and the pipeline has no AWS credentials at all. That tells me the code is well formed and passes the scans. It does not tell me the cluster comes up, because I have not applied this to a real AWS account, and the README says so on its first line.

## What went wrong on the way

- Trivy failed after `terraform init`, because it started scanning the example folders inside the downloaded modules. Running the scan before init fixed it.
- Trivy flagged three things: the public API endpoint, open outbound traffic from the nodes and the VPC module's default network ACLs. Each one is accepted in `.trivyignore` with the reason written next to it.
- The default Kubernetes version went stale within weeks. I bumped it, and the README now tells you to check the EKS version calendar before you apply.

## What it doesn't do yet

- Nothing scales the GPU group by itself. The group is tagged for a cluster autoscaler, but I haven't added one, so scaling is manual.
- State is local. A team would keep it in S3 with locking.
- The NVIDIA device plugin is installed by hand, not by Terraform or GitOps.
- Outbound traffic is open instead of going through VPC endpoints.
- A real apply in a sandbox account, with a billing alarm set first, hasn't happened.
