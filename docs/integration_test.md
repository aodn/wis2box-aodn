# Integration Test

The integration test is a controlled, non-production test dataset used to verify
that wis2box-aodn can publish metadata and, later, process data end to end
without using real operational station records.

It exists to answer practical deployment questions:

- can the GitHub Actions metadata publishing workflow update wis2box metadata?
- can discovery metadata be added and published through the wis2box CLI?
- can station metadata be published against the expected WIS2 topic hierarchy?
- can future test input data move through the data pipeline without affecting
  production datasets?

The test metadata uses a dedicated discovery collection and station file:

- `integration-test.yml`
- `integration_test.csv`

Keeping this dataset separate makes it possible to test workflow, CLI, and
pipeline behavior repeatedly in non-production while keeping production clean.
For that reason, integration test metadata is explicitly excluded from the
production workflow.


## Metadata Publishing

### Metadata Scope

Integration test metadata exists only to support non-production validation. It
must not be published to the production wis2box environment.

The integration test metadata files are:

- `wis2-pipeline/wis2box-data/metadata/discovery/integration-test.yml`
- `wis2-pipeline/wis2box-data/metadata/station/integration_test.csv`

The integration test discovery collection uses:

- collection stem: `integration-test`
- metadata identifier: `urn:wmo:md:au-imos:integration-test`
- topic hierarchy: `au-imos/data/core/ocean/surface-based-observations/integration-test`

### Metadata Publishing in Non-Production

The non-production workflow is:

- `.github/workflows/publish_metadata_non_prod.yml`
- GitHub environment: `edge`
- ECS cluster/family: `wis2box-edge`

Non-production intentionally includes integration test metadata. The workflow
sets `INCLUDE_INTEGRATION_TEST=true` when it runs:

- `publish_discovery_metadata.sh`
- `publish_station_metadata.sh`

This enables the scripts to publish:

- `metadata/discovery/integration-test.yml`
- `metadata/station/integration_test.csv`

When only integration test discovery metadata changes, the non-production
workflow publishes the `integration-test` discovery collection. When
`integration_test.csv` changes, the workflow runs station metadata publishing.

Manual `full_publish=true` runs in non-production also include integration test
metadata.

### Metadata Publishing in Production

The production workflow is:

- `.github/workflows/publish_metadata_prod.yml`
- GitHub environment: `production`
- ECS cluster/family: `wis2box-production`

Production excludes integration test metadata in two places.

First, the workflow filters integration test files during changed-file
detection:

- `metadata/discovery/integration-test.yml`
- `metadata/station/integration_test.csv`

If a push to `main` changes only those integration test files, the production
workflow stops after the detect job. It does not resolve ECS, update container
metadata, or publish metadata.

Second, the production workflow does not set `INCLUDE_INTEGRATION_TEST=true`.
The publish scripts therefore use their default behavior and skip integration
test metadata.

This also applies to manual `full_publish=true` production runs: all production
metadata is published, but integration test metadata remains excluded by the
scripts.

### Metadata Script Controls

`publish_discovery_metadata.sh` skips the `integration-test` collection unless
`INCLUDE_INTEGRATION_TEST=true` is set.

`publish_station_metadata.sh` skips `integration_test.csv` unless
`INCLUDE_INTEGRATION_TEST=true` is set.

Expected behavior:

| Workflow | `INCLUDE_INTEGRATION_TEST` | Integration test metadata |
|---|---|---|
| Non-production | `true` | Published |
| Production | unset | Skipped |

### Metadata Operational Notes

Use non-production to verify integration test metadata changes before merging to
`main`.

Do not set `INCLUDE_INTEGRATION_TEST=true` in the production workflow. That
variable is the explicit guard that prevents test metadata from being published
to production.

If integration test metadata appears in production, check:

- whether `INCLUDE_INTEGRATION_TEST=true` was accidentally added to
  `.github/workflows/publish_metadata_prod.yml`
- whether the production changed-file filters still exclude
  `integration-test.yml` and `integration_test.csv`
- whether the publish scripts still skip integration test metadata by default

## Data Pipeline Integration Test

TODO: implement data pipeline integration test.

The intended scope is to validate the path from test input data through wis2box
processing and publication, using integration test metadata and station records
in non-production only.
