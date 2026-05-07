# IMOS WIS2.0 Terraform

This directory contains the Terraform configurations for deploying the wis2box-aodn infrastructure on AWS.

The deployment uses the [appdeploy `wis2` Terraform module](https://github.com/aodn/appdeploy/tree/main/tf/wis2), which provisions a complete, production-ready AWS stack.

## Key Infrastructure Components

| Resource | Purpose |
|---|---|
| ECS Fargate cluster & service | Runs the 7-container wis2box task (4 vCPU / 8 GiB) |
| Application Load Balancer | HTTPS ingress, TLS termination, listener rules |
| Network Load Balancer | TCP:1883 ingress for the Mosquitto MQTT broker |
| CloudFront distribution | CDN with WAF, HSTS, and custom error pages |
| EFS volumes (×7) | Encrypted persistent storage across 3 AZs |
| S3 config bucket | Stores environment variable files for the ECS task |
| Route 53 records | A-alias records for app (→ CloudFront) and broker (→ NLB) |
| SSM Parameter Store | Shared infrastructure references (VPC, certs, WAF, etc.) |

For a full architecture description, diagrams, and deployment details see [`docs/infrastructure.md`](../docs/infrastructure.md).
