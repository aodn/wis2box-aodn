# WIS2 Infrastructure Deployment

The WIS2 infrastructure was deployed on AODN AWS account using Terraform code. The main code uses a Terraform module [appdeploy](https://github.com/aodn/appdeploy/tree/main/tf/wis2) that deploys a wis2box application container on AWS.

## Overview

The module provisions a complete, production-ready AWS stack covering:

- **Container hosting** — ECS Fargate cluster and service running the WIS2box application and Mosquitto MQTT broker
- **Message brokering** — Mosquitto (MQTT) broker exposed via a dedicated Network Load Balancer for WIS2 data exchange
- **Content delivery** — CloudFront CDN with WAF, HSTS, and custom error pages in front of the application
- **Persistent storage** — encrypted EFS volumes, an S3 config bucket, and an optional S3 data bucket with disaster-recovery replication
- **DNS** — Route 53 records for both the web application and the MQTT broker endpoint

The module is designed as a self-contained, reusable unit. All shared infrastructure (VPC, subnets, certificates, hosted zone, ALB) is resolved at plan/apply time via **AWS SSM Parameter Store** — no hard-coded account-specific values are required.

---

## Architecture Diagram

The diagram below shows all AWS services deployed by this module and their relationships.

```mermaid
flowchart TD
    subgraph inet["🌐 Internet"]
        WebClient(["Web Browser\nHTTPS / HTTP"])
        MQTTClient(["MQTT Client\nTCP 1883"])
    end

    subgraph dns["Route 53"]
        R53App["A record\napp aliases → CloudFront"]
        R53Broker["A record\nbroker domain → NLB"]
    end

    subgraph cdn["CloudFront  (Global Edge — us-east-1)"]
        CF["CloudFront Distribution\n• aliases: app_hostnames\n• viewer protocol: HTTPS only\n• TLS 1.2+ (SNI)\n• access logs → S3 log bucket"]
        WAF(["WAF WebACL\n(shared, global)\nfrom SSM /apps/global/waf"])
        ACMGlobal(["ACM Wildcard Cert\nus-east-1\nfrom SSM /core/wildcard_id"])
        CFOriginPolicy["Origin Request Policy\n• headers: allViewer\n• query strings: all\n• cookies: all"]
        CFRespPolicy["Response Headers Policy\nHSTS: max-age=31536000\nincludeSubDomains; preload"]
    end

    subgraph public["Public Subnets  (×3 AZs)"]
        ALB["Application Load Balancer\n• HTTP:80 → HTTPS redirect 301\n• HTTPS:443 TLS 1.3\n• deletion protection in production\n• (created or shared via SSM)"]
        ACMRegional(["ACM Wildcard Cert\nregional\nfrom SSM /core/wildcard_id"])
        NLB["Network Load Balancer\nwis2box-broker\nTCP:1883\n(always created)"]
    end

    subgraph alb_rules["ALB Listener Rules  (HTTPS:443)"]
        TG_App["Target Group: app\nHTTP · IP · port 80 or 9000\nhealth check: /health"]
        TG_Broker["Target Group: tg_broker\nTCP · IP · port 1883"]
        TG_Extra["Target Group: additional_public_tg\n(one per additional_public_containers)\n(optional)"]
        Rule_Redirect["Rule: context_path redirect\n/ → context_path (302)\n(if context_path set)"]
        Rule_App["Rule: host-header match\nper app_hostname → TG app"]
        Rule_CF["Rule: additional_host_rules\n(CloudFront internal hostnames)\n→ TG app"]
        Rule_Extra["Rule: host + path pattern\n→ TG additional_public_tg\n(optional)"]
    end

    subgraph ecs["ECS Fargate Service  (Private Subnets ×3 AZs)"]
        subgraph task["ECS Task Definition"]
            AppCtr["app container\nimage: ECR (digest/tag)\nport: 9000\nenv: variables + secrets + env files"]
            NginxCtr["nginx proxy\n(optional)\nport: 80\nproxy_pass → app:9000"]
            MosqCtr["mosquitto\nMQTT broker\nport: 1883"]
            ExtraCtr["extra containers\n(optional)\nadditional_public_containers"]
        end
        ASG["Auto Scaling\nCPU target: 50%\nmin / max: 1 / 10\n(configurable)"]
        CircuitBreaker["Deployment circuit breaker\n+ automatic rollback"]
        ECSExec["ECS Exec enabled\n(interactive shell access)"]
    end

    subgraph storage["Storage"]
        S3Cfg["S3 Config Bucket\nappconfig-{app}-{env}\n• versioned\n• env files (MD5-keyed objects)\n• task exec role: GetObject"]
        S3Data["S3 Data Bucket\ndata-{app}-{env}\n(optional)\n• versioned\n• CORS configurable\n• task role: full CRUD"]
        EFS["EFS Volume(s)\n• encrypted at rest\n• backup enabled\n• mount targets ×3 AZs\n• access via EFS access points\n• NFS ingress from ECS SG only"]
    end

    subgraph dr["Disaster Recovery Account  (optional)"]
        S3Replica["S3 Replica Bucket\nGLACIER storage class\ncross-account replication"]
    end

    subgraph config["Configuration & Registry  (resolved at deploy time)"]
        SSM["SSM Parameter Store\n/core/vpc_id · vpc_cidr\n/core/subnets_public · subnets_private\n/core/zone_domain · zone_id\n/core/wildcard_id/{domain}\n/apps/global/waf\n/apps/global/oac/shared_s3_oac\n/apps/alb/{name}/* (shared ALB)\n/apps/{app}/{env}/image_digest"]
        ECR["ECR Registry\n851725428481.dkr.ecr\n.ap-southeast-2.amazonaws.com\nimage: {repo}@{digest}"]
    end

    subgraph errpages["Error Pages  (optional)"]
        S3Err["S3 Bucket: aodn-error-pages\n403.html\nvia shared OAC"]
    end

    %% DNS flow
    WebClient -->|"DNS query"| R53App
    MQTTClient -->|"DNS query"| R53Broker
    R53App -->|"A alias"| CF
    R53Broker -->|"A alias"| NLB

    %% CDN → ALB
    WAF -. "filters requests" .-> CF
    ACMGlobal -. "viewer cert (SNI)" .-> CF
    CFOriginPolicy -. "attached" .-> CF
    CFRespPolicy -. "attached" .-> CF
    CF -->|"HTTPS origin\nforward headers/QS/cookies"| ALB
    CF -->|"403 custom error\n/_cf-errors/403.html\n(edge/staging/production)"| S3Err

    %% ALB certs and rules
    ACMRegional -. "HTTPS listener cert" .-> ALB
    ALB --> Rule_Redirect
    ALB --> Rule_App
    ALB --> Rule_CF
    ALB --> Rule_Extra
    Rule_Redirect --> TG_App
    Rule_App --> TG_App
    Rule_CF --> TG_App
    Rule_Extra --> TG_Extra

    %% NLB
    NLB -->|"TCP:1883"| TG_Broker

    %% TGs → containers
    TG_App -->|"HTTP port 80"| NginxCtr
    TG_App -->|"HTTP port 9000\n(nginx disabled)"| AppCtr
    TG_Broker -->|"TCP port 1883"| MosqCtr
    TG_Extra -->|"container port"| ExtraCtr
    NginxCtr -->|"proxy_pass :9000"| AppCtr

    %% ECS storage
    AppCtr -->|"reads env files at startup\ntask exec role: s3:GetObject"| S3Cfg
    AppCtr -->|"read/write app data\ntask role: full CRUD\n(optional)"| S3Data
    AppCtr -->|"NFS mount :2049\nvia EFS access point"| EFS

    %% Image
    ECR -->|"image pull on task start\ndigest pinned"| AppCtr

    %% DR replication
    S3Data -->|"async replication\n(optional)"| S3Replica

    %% SSM at deploy time
    SSM -. "Terraform data sources\n(plan / apply only)" .-> ALB
    SSM -. "VPC / subnet IDs" .-> ecs
    SSM -. "image_digest" .-> AppCtr
    SSM -. "global cert + WAF + OAC" .-> cdn

    %% Scaling
    ASG -. "scales" .-> task
```

---

## Deployed Services

| Service | AWS Resource | Defined in | Purpose |
|---------|-------------|-----------|---------|
| ECS Cluster | `module.cluster` (`terraform-aws-modules/ecs`) | `cluster.tf` | Fargate cluster with Container Insights |
| ECS Service | `module.service` (`terraform-aws-modules/ecs`) | `service.tf` | Runs the task definition with autoscaling |
| Application Load Balancer | `module.alb` (`terraform-aws-modules/alb`) | `alb.tf` | HTTPS ingress, TLS termination, listener rules |
| Network Load Balancer | `module.nlb` (`terraform-aws-modules/alb`) | `nlb.tf` | TCP:1883 ingress for MQTT broker |
| CloudFront Distribution | `aws_cloudfront_distribution.this` | `cloudfront.tf` | CDN, WAF, HSTS, custom error pages |
| CloudFront Origin Request Policy | `aws_cloudfront_origin_request_policy` | `cloudfront.tf` | Controls headers/QS/cookies forwarded to ALB |
| CloudFront Response Headers Policy | `aws_cloudfront_response_headers_policy` | `cloudfront.tf` | Enforces HSTS on all responses |
| S3 Config Bucket | `module.config_bucket` | `bucket.tf` | Stores environment variable files for ECS |
| S3 Data Bucket | `module.data_bucket` | `bucket.tf` | Application data (optional) |
| S3 Replication | `aws_s3_bucket_replication_configuration` | `bucket.tf` | Cross-account DR replication (optional) |
| EFS Volumes | `module.efs_volumes` (`terraform-aws-modules/efs`) | `efs.tf` | Persistent container storage across 3 AZs |
| Route 53 — app record | `aws_route53_record.app` | `route53.tf` | A alias → CloudFront for each app hostname |
| Route 53 — broker record | `aws_route53_record.broker` | `route53.tf` | A alias → NLB for MQTT broker domain |
| ALB Target Group (app) | `aws_lb_target_group.app` | `alb.tf` | Routes HTTP traffic to app/nginx container |
| ALB Target Group (broker) | `aws_lb_target_group.tg_broker` | `nlb.tf` | Routes TCP:1883 to mosquitto container |
| ALB Target Group (extra) | `aws_lb_target_group.additional_public_tg` | `alb.tf` | Routes traffic to extra public containers |
| ALB Listener Rules | `aws_lb_listener_rule.*` | `alb.tf` | host-header + path-pattern matching rules |

---

## Key Components

### ECS Fargate Cluster (`cluster.tf`)

The ECS cluster is created with CloudWatch **Container Insights** enabled. It supports both `FARGATE` and `FARGATE_SPOT` capacity providers (50/50 weight by default).

The `create_cluster` variable lets you either create a dedicated cluster or attach the service to an existing one by providing its ARN via `cluster_arn`. A `null_resource` precondition enforces that exactly one of these options is set.

### ECS Fargate Service (`service.tf`)

The service runs the WIS2box task definition inside private subnets. Key configuration:

| Setting | Default | Notes |
|---------|---------|-------|
| Capacity provider | `FARGATE` (production) / `FARGATE_SPOT` (others) | Controlled by `var.environment` |
| CPU | 512 | Configurable via `var.cpu` |
| Memory | 1024 MiB | Configurable via `var.memory` |
| Autoscaling | Enabled, 1–10 tasks | CPU target tracking at 50% |
| Deployment | min 66%, max 200% healthy | Circuit breaker + auto rollback |
| ECS Exec | Enabled | Allows `aws ecs execute-command` for live debugging |
| Steady-state wait | Enabled | Terraform waits up to 15 min for deployment |

**Task container layout:**

| Container | Port | Always present | Description |
|-----------|------|---------------|-------------|
| `app` | 9000 | ✅ | Main WIS2box application, image from ECR |
| `mosquitto` | 1883 | ✅ | Eclipse Mosquitto MQTT broker for WIS2 data exchange |
| `nginx` | 80 | Optional (`nginx_proxy = true`) | Reverse proxy in front of the app container |
| `extra` | varies | Optional | Any additional containers via `extra_container_definitions` |
| `additional_public` | varies | Optional | Extra containers with their own ALB target groups |

The ALB target group points at the **nginx** container (port 80) when `nginx_proxy = true`, otherwise directly at the **app** container (port 9000). The NLB target group always points at the **mosquitto** container (port 1883).

**Security group rules** for the ECS service are tightly scoped:

| Direction | Port | Source/Destination | Reason |
|-----------|------|--------------------|--------|
| Ingress | 80 or 9000 | ALB security group | HTTP from load balancer |
| Ingress | 1883 | NLB security group | MQTT from broker load balancer |
| Ingress | varies | ALB security group | Additional public containers |
| Egress | 443 | 0.0.0.0/0 | Outbound HTTPS (ECR, SSM, S3 endpoints) |
| Egress | 2049 | VPC CIDR | NFS to EFS mount targets |

### Application Load Balancer (`alb.tf`)

The ALB operates in public subnets and handles all HTTP/HTTPS web traffic. It can be **created by this module** (default) or **shared** with other applications by setting `alb_parameter_name` to a key in SSM that holds an existing ALB's DNS name, listener ARN, security group ID, and zone ID.

**Listener rules** (evaluated in order):

1. `context_path` — if `var.context_path` is set, redirects bare `/` requests to the configured sub-path (HTTP 302)
2. `app_fgate` — host-header match per entry in `var.app_hostnames` → forwards to TG `app`
3. `cloudfront` — host-header match per entry in `var.additional_host_rules` (e.g. internal CloudFront hostnames) → forwards to TG `app`
4. `additional_listener_rule` — host + path-pattern match per `additional_public_containers` entry → forwards to its dedicated target group

### Network Load Balancer (`nlb.tf`)

A dedicated NLB named `wis2box-broker` (configurable via `nlb_name`) accepts raw TCP connections on port **1883** and forwards them to the `mosquitto` container in the ECS service. This port is the standard MQTT port used by WIS2 clients to subscribe to data notifications.

Deletion protection is enabled in production. The NLB is always created by this module (unlike the ALB, which can be shared).

### CloudFront Distribution (`cloudfront.tf`)

CloudFront serves as the public entry point for web traffic. It uses:

- A **global ACM wildcard certificate** (from `us-east-1`, fetched from SSM) for viewer connections
- A **shared WAF WebACL** (fetched from SSM `/apps/global/waf`) attached to the distribution
- The **ALB** as its primary origin (HTTPS-only, TLS 1.2+)
- Optional **additional origins** for other backends via `additional_origins`
- An **HSTS response headers policy** enforcing `max-age=31536000; includeSubDomains; preload`
- **CloudFront access logging** to `log-bucket-{account_id}`, prefixed by app/environment
- **Custom error page** for 403 responses (enabled automatically on edge/staging/production), served from an S3 origin via a shared Origin Access Control (OAC) fetched from SSM

The `default_cache_policy_id` defaults to the AWS-managed **CachingDisabled** policy — meaning CloudFront acts purely as a CDN shield and request router, not a cache.

### S3 Buckets (`bucket.tf`)

**Config Bucket** (`appconfig-{app}-{env}`):
- Always created; holds environment variable files placed in `environment_files/` alongside the Terraform code
- Files are uploaded as S3 objects with an MD5-hash prefix in the key — Terraform detects content changes and re-uploads automatically
- The ECS task execution role receives `s3:GetObject` and `s3:GetBucketLocation` permissions on this bucket
- Files are loaded into the container at startup via the ECS `environmentFiles` mechanism

**Data Bucket** (`data-{app}-{env}`, optional — `enable_data_bucket = true`):
- The ECS task role receives full CRUD permissions (`GetObject`, `PutObject`, `DeleteObject`, `ListBucket`, etc.)
- CORS rules can be applied via `data_bucket_cors_rules`
- Cross-account S3 replication to a DR account is supported via `enable_data_bucket_replication` — replicas are stored in GLACIER
- In the `edge` environment, `force_destroy = true` is set so the bucket can be deleted by Terraform without manual emptying

### EFS Volumes (`efs.tf`)

EFS volumes are defined as a map via `var.efs_volumes`. For each entry the module creates:

- An EFS file system (encrypted at rest, backup policy enabled by default)
- Mount targets in each of the three private subnets (one per AZ)
- EFS access points per the `access_points` map inside each volume definition
- A security group that only permits NFS ingress (port 2049) from the ECS service's security group

Volume configuration can be DRY'd up with `efs_defaults` — values set there apply to every volume unless overridden per-volume.

### Route 53 (`route53.tf`)

Two record types are created:

| Record | Type | Points to |
|--------|------|-----------|
| Per alias in CloudFront distribution that matches the hosted zone | A (alias) | CloudFront distribution |
| `var.broker_domain_name` | A (alias) | NLB DNS name |

The hosted zone is resolved from SSM (`/core/zone_domain`, `/core/zone_id`) — no zone ID needs to be passed in as a variable.

### SSM Parameter Store Integration (`parameters.tf`)

All account-level and environment-level values are consumed as **Terraform data sources** at plan/apply time. They are never stored in the module's state, keeping the module portable across accounts.

| SSM path | Used for |
|----------|---------|
| `/core/vpc_id` | VPC for all resources |
| `/core/vpc_cidr` | Security group CIDR rules |
| `/core/subnets_public` | ALB and NLB subnets |
| `/core/subnets_private` | ECS service and EFS subnets |
| `/core/zone_domain` | Route 53 hosted zone name |
| `/core/zone_id` | Route 53 hosted zone ID |
| `/core/wildcard_id/{domain}` | Regional ACM cert ARN for ALB |
| `/apps/global/waf` *(us-east-1)* | WAF WebACL ID for CloudFront |
| `/apps/global/oac/shared_s3_oac` *(us-east-1)* | Shared S3 OAC for CloudFront error pages |
| `/apps/global/wildcard_id/{domain}` *(us-east-1)* | Global ACM cert ARN for CloudFront |
| `/apps/alb/{name}/*` | Shared ALB details (when `alb_parameter_name` is set) |
| `/apps/{app}/{env}/image_digest` | ECR image digest (when `var.image` is empty) |

### Image Resolution

The module supports three ways to specify the container image:

1. **Digest string** (`image = "sha256:abc123..."`) — module prepends `{ecr_registry}/{ecr_repository}@`
2. **Full image URI** (`image = "123456789.dkr.ecr.ap-southeast-2.amazonaws.com/my-repo:tag"`) — used as-is
3. **SSM-resolved digest** (`image = ""`, default) — the module reads the digest from SSM at `/apps/{app}/{env}/image_digest` (or a custom `image_digest_parameter_name`). This enables **image-only deployments** via a separate CI/CD step that updates the SSM parameter — no Terraform re-run required.

---

## Environment-Specific Behaviour

| Setting | `edge` / `staging` | `production` |
|---------|--------------------|-------------|
| Capacity provider | `FARGATE_SPOT` (100%) | `FARGATE` (100%) |
| ALB/NLB deletion protection | Disabled | Enabled |
| CloudFront custom error page | Enabled | Enabled |
| S3 data bucket `force_destroy` | Enabled | Disabled |

---

## Usage

```hcl
module "wis2" {
  source = "path/to/tf/wis2"

  # Required
  app_name           = "wis2box"
  environment        = "production"
  aws_region         = "ap-southeast-2"
  ecr_repository     = "wis2box"
  broker_domain_name = "wis2-broker.example.aodn.org.au"

  # DNS / CDN
  app_hostnames = ["wis2.example.aodn.org.au"]
  aliases       = ["wis2.example.aodn.org.au"]

  # Compute
  cpu    = 1024
  memory = 2048

  # Environment files placed in ./environment_files/
  environment_files = ["wis2box.env"]

  # Persistent storage
  efs_volumes = {
    wis2box-data = {
      access_points = {
        root = {
          posix_user    = { uid = 1000, gid = 1000 }
          root_directory = { path = "/data" }
        }
      }
    }
  }

  # Optional: enable application data bucket
  enable_data_bucket = true

  # Optional: share an existing ALB
  # alb_parameter_name = "shared-alb"
}
```

---