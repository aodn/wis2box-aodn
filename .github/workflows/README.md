# GitHub Actions Workflows

## `publish_metadata_non_prod.yml` — Publish Metadata to Non-Production (Edge)

### Purpose

Automatically deploys dataset discovery metadata and station metadata to the **non-production (edge) wis2box environment** whenever metadata files are added or modified in a `feature` or `fix` branch. Only changed files are published — not the entire metadata directory.

### Trigger

| Event | Branches | Path filter |
|-------|----------|-------------|
| `push` | `feature/**`, `fix/**` | `wis2-pipeline/wis2box-data/metadata/**` |
| `workflow_dispatch` | selected manually | none |

> `main` is intentionally excluded — production deployments will be handled by a separate workflow.

Manual runs support a `full_publish` input. When enabled, the workflow updates the metadata files from the selected branch, publishes all discovery metadata, and publishes station metadata. This is intended for recovery after a failed run or an ECS outage.

### Concurrency

A `concurrency` group (`metadata-publish`) ensures only one run executes at a time. In-progress runs are **not** cancelled — the next run queues and waits.

### Steps

```
push to feature/** or fix/**
        │
        ▼
Job: Detect metadata changes
1. Checkout (fetch-depth: 2)
        │
        ▼
2. Detect changed files
   ├── discovery/*.yml  →  outputs: collections (space-separated stems)
   └── station/*.csv  →  outputs: station_changed (true/false)
   └── skipped when manual full_publish=true
        │
        ▼
Job: Resolve running ECS task
3. Configure AWS credentials (OIDC)
        │
        ▼
4. Resolve running ECS task ARN dynamically
        │
        ▼
Job: Update metadata in container
5. Update metadata in container
   └── Clones the triggering branch into the container via DEPLOY_BRANCH env var
        │
        ▼
Job: Publish discovery metadata
6a. Publish changed discovery collections   (skipped if no .yml changed)
        │
        ▼

Job: Publish station metadata
6b. Publish changed station metadata        (skipped if station/*.csv unchanged)

Manual full_publish=true:
6a. Publish all discovery collections
6b. Publish station metadata
```

### Publish logic

| What changed | Step 6a (discovery) | Step 6b (station) |
|---|---|---|
| Only discovery `.yml` files | ✅ Runs — publishes only changed collections | ⏭️ Skipped |
| Only station `*.csv` files | ⏭️ Skipped | ✅ Runs |
| Both | ✅ Runs first | ✅ Runs after discovery succeeds |
| Neither | ⏭️ Skipped | ⏭️ Skipped |

### AWS Infrastructure

| Resource | Value |
|----------|-------|
| AWS Region | `ap-southeast-2` |
| ECS Cluster | `wis2box-edge` |
| ECS Container | `wis2box-management` |
| IAM Role | GitHub Environment Variables |

> The ECS task ARN is resolved dynamically at runtime — it is not hardcoded.

---

## `publish_metadata_prod.yml` — Publish Metadata to Production

### Purpose

Automatically deploys production discovery and station metadata to the **production wis2box environment** when metadata changes land on `main`. Integration test metadata is excluded from production publishing.

### Trigger

| Event | Branches | Path filter |
|-------|----------|-------------|
| `push` | `main` | `wis2-pipeline/wis2box-data/metadata/**` |
| `workflow_dispatch` | selected manually | none |

Manual runs support `full_publish=true`, which publishes all production discovery metadata and station metadata. The workflow does not set `INCLUDE_INTEGRATION_TEST=true`, so `integration-test.yml` and `integration_test.csv` are skipped by the publish scripts.

### Production Exclusions

- `metadata/discovery/integration-test.yml` is filtered out during changed-file detection.
- `metadata/station/integration_test.csv` is filtered out during changed-file detection.
- If only integration test metadata changes, the production workflow stops after the detect job.
- Full publish still relies on the scripts' default behavior, which skips integration test metadata unless `INCLUDE_INTEGRATION_TEST=true` is set.

### AWS Infrastructure

| Resource | Value |
|----------|-------|
| AWS Region | `ap-southeast-2` |
| ECS Cluster | `wis2box-production` |
| ECS Task Family | `wis2box-production` |
| ECS Container | `wis2box-management` |
| IAM Role | GitHub Environment Variable `METADATA_PUBLICATION_IAM_ROLE` in the `production` environment |

---

## Corresponding Scripts

All scripts live in `wis2-pipeline/wis2box-data/scripts/` and run **inside the `wis2box-management` ECS container**.

### `update_metadata.sh`

Pulls the latest metadata from GitHub into the container at `/data/wis2box/metadata/`.

- Backs up existing metadata before applying changes
- Clones the branch specified by the `DEPLOY_BRANCH` environment variable (defaults to `main` when run manually)
- Restores the backup automatically if any step fails

```bash
# Manual use (clones main)
./update_metadata.sh

# Called by the workflow (clones the triggering branch)
DEPLOY_BRANCH=feature/my-branch ./update_metadata.sh
```

### `publish_discovery_metadata.sh`

Publishes dataset discovery metadata (`.yml` files) to wis2box.

- With arguments: publishes only the specified collections
- Without arguments: publishes all collections in the discovery directory (manual full-publish mode)

```bash
# Publish specific collections (used by the workflow)
./publish_discovery_metadata.sh wave-buoys cicd-test

# Publish all collections (manual use)
./publish_discovery_metadata.sh
```

### `publish_station_metadata.sh`

Publishes station metadata (`station_list.csv`) to wis2box, associating stations with the wave-buoys topic hierarchy.

```bash
./publish_station_metadata.sh
```
