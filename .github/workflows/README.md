# GitHub Actions Workflows

This directory contains CI/CD workflows for publishing WIS 2.0 metadata to the wis2box environments.

## Workflows

### `publish_metadata_non_prod.yml` — Publish metadata to non-production (edge)

**Triggers:**
- Push to `feature/**` or `fix/**` branches when files under `wis2-pipeline/wis2box-data/metadata/` change
- Manual dispatch via `workflow_dispatch` (with optional `full_publish` flag)

**What it does:**
1. Detects which discovery (`.yml`) and station (`.csv`) metadata files changed
2. Resolves the running ECS task in the `wis2box-edge` cluster
3. Clones the branch into the wis2box management container to update metadata files
4. Publishes changed (or all, if `full_publish=true`) discovery metadata
5. Publishes station metadata if station CSV files changed

**Environment:** `edge`

---

### `publish_metadata_prod.yml` — Publish metadata to production

**Triggers:**
- Push to `main` branch when files under `wis2-pipeline/wis2box-data/metadata/` change
- Manual dispatch via `workflow_dispatch` (with optional `full_publish` flag)

**What it does:**
1. Detects which discovery and station metadata files changed (excludes `integration-test` collection and `integration_test.csv`)
2. Resolves the running ECS task in the `wis2box-production` cluster
3. Clones the branch into the wis2box management container to update metadata files
4. Publishes changed (or all, if `full_publish=true`) discovery metadata
5. Publishes station metadata if station CSV files changed

**Environment:** `production`

---

## Common Architecture

Both workflows share the same job structure:

| Job | Purpose |
|-----|---------|
| `detect_metadata_changes` | Determines which metadata files were added or modified |
| `resolve_ecs_task` | Finds the running ECS task ARN for the target cluster |
| `update_metadata_in_container` | Clones the repo branch into the container and runs `update_metadata.sh` |
| `publish_discovery_metadata` | Publishes discovery metadata via `publish_discovery_metadata.sh` |
| `publish_station_metadata` | Publishes station metadata via `publish_station_metadata.sh` |

## Authentication

Workflows use OIDC (`id-token: write`) to assume an IAM role specified by the `METADATA_PUBLICATION_IAM_ROLE` environment variable, configured per GitHub environment.

## Manual Recovery

After an ECS outage or failed publish, trigger the workflow manually with `full_publish=true` to republish all metadata from the selected branch.
