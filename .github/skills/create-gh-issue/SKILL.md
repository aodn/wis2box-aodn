---
name: create-gh-issue
description: >
  Use when creating, filing, or logging a GitHub issue in aodn/backlog.
  Handles user stories, feature requests, enhancements, tasks, bugs, epics,
  and technical debt items. Automatically formats the title with the correct
  prefix and T-level tags, populates every section of the AODN body template,
  applies appropriate labels, and adds the new issue to the AODN Pipeline
  Uplift Team project board (#72).
---

# Create Issue

Create a GitHub issue for the AODN Pipeline Uplift Team project following the appropriate template.

## Instructions

When the user describes an issue, determine the type, format the title correctly, fill in the template, create the issue, and add it to the project board.

### Workflow

1. Determine the issue type (see **Issue Types** below)
2. Format the title following the **Title Conventions**
3. Read `.github/ISSUE_TEMPLATE/pipeline-general-template.md` and fill it in
4. Write the content to `NewIssue.md`
5. Create the issue and add it to the project board (see **Using GitHub CLI**)

## Issue Types

| Type | Title prefix | When to use |
|---|---|---|
| User Story | `AS A … I WANT … SO THAT …` | A new capability from a user's perspective |
| Feature / Enhancement | `✨` | A concrete deliverable or implementation task |
| Task | `📋(TASK)` | An operational or process task |
| Epic | plain title + `[epic]` tag | Too large for one iteration, needs breakdown |
| Bug | plain title + `[bug]` tag | Something broken |
| Technical Debt | plain title + `[technical debt]` tag | Clean-up or refactoring |

## Title Conventions

Titles follow this structure:

```
<prefix> <Short description> <[T-level tags]> <[type tag]>
```

- **T-level tags** categorise the work area, e.g. `[T3 - ARDC Waves]`, `[T3 - Reef Network]`, `[T1 - IMOS, T2 - O&M - Continuous Improvement]`
- **Type tags**: `[epic]`, `[bug]`, `[technical debt]`, `[DEVOPS, general backlog]`
- Story points are set via **labels only** (not in the title)

### Examples

```
AS A wave data user I WANT NRT buoy data gaps filled SO THAT my analysis is complete [T3 - ARDC Waves]
✨WIS2.0 Prefect Flow
📋(TASK) Apply mask into GSLA particle PNG generation
Test implementation of WIS2.0 Wave Buoys Collection [epic]
Scheduled diff check between CO files and NetCDF files [technical debt]
```

## Project Areas (Project field)

Use the appropriate project area when creating the issue:

| Area | Use for |
|---|---|
| `WIS2` | WIS 2.0 / wis2box work |
| `Cloud Optimised` | Zarr, Parquet, CO library |
| `Waves` | Wave buoy data, ARDC Waves |
| `NRMN` | Reef Life Survey / NRMN data |
| `BAU` | Business as usual, maintenance |
| `Outreach` | Papers, workshops, demos |

## Body Template

Use `.github/ISSUE_TEMPLATE/pipeline-general-template.md` as the body. Fill every section:

- **User Story** — AS A / I WANT / SO THAT (even for non-story issues, state the goal)
- **Acceptance Criteria** — numbered list of verifiable outcomes
- **Notes** — assumptions, constraints, background links
- **Tasks** — checkbox list of sub-tasks; always include the DOD checklist link
- **PRs** — leave as template placeholder; include PR review guidelines link
- **Dependencies** — upstream issues or external blockers

## Using GitHub CLI (gh)

### Step 1 — Create the issue

```bash
# Default repo is aodn/backlog; specify explicitly if needed
gh issue create -R aodn/backlog \
  --title "<formatted title>" \
  --body-file NewIssue.md \
  --label "type - development" \
  --label "2 story points"
```

The command returns the new issue URL — copy it for Step 2.

### Step 2 — Add to the AODN Pipeline Uplift Team project (#72)

```bash
gh project item-add 72 --owner aodn --url <issue-url>
```

### Common Labels

- `type - development` — New feature or system
- `type - operational` — Maintenance or operational work
- `type - testing & release` — Manual testing and deployment
- `Epic` — Too large for an iteration, needs breakdown
- `Blocked` — Cannot be worked on; has blocking dependencies
- `1 story points`, `2 story points`, `3 story points`, `5 story points`, `8 story points` — Complexity estimate

### Other Useful Commands

```bash
# List open issues
gh issue list -R aodn/backlog

# View an issue
gh issue view <issue-number> -R aodn/backlog

# Add a comment
gh issue comment <issue-number> -R aodn/backlog --body "Comment text"

# List items currently in project #72
gh project item-list 72 --owner aodn
```
