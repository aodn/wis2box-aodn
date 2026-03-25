# Create Issue

Create a GitHub issue for the project following the appropriate template.

## Instructions

When the user describes an issue, determine the appropriate template and create a properly formatted issue file:

### Template Selection

create an common template under `.github/ISSUE_TEMPLATE/`

### Workflow

1. Read the appropriate template from `.github/ISSUE_TEMPLATE/`
2. Create the issue content following the template structure:
   - Use proper user story format: AS A/I WANT/SO THAT
   - Include acceptance criteria as checklist
   - Add relevant sections (sub-tasks, related tickets, etc.)
3. Write the content to `NewIssue.md` (or descriptively named file)
4. Show the user the `gh` command to create the issue:
   ```bash
   gh issue create --title "<title>" --body-file NewIssue.md
   ```
5. Let the user run the command, which will create the issue and return the GitHub issue URL

## User Story Format

All issues must follow:

```
AS A <type of user>
I WANT <some goal>
SO THAT <some reason>
```

## Using GitHub CLI (gh)

After the issue file is created, use the GitHub CLI to create the issue:

### Checking Which Repository Will Be Used

```bash
# View current default repository
gh repo set-default --view

# Change default repository (interactive)
gh repo set-default
```


### Basic Usage

```bash
# Uses default repository (aodn/backlog)
gh issue create --title "Issue title" --body-file NewIssue.md

# Explicitly specify repository
gh issue create -R aodn/backlog --title "Issue title" --body-file NewIssue.md
```

### With Labels and Milestone

```bash
gh issue create --title "Add dark mode" \
  --body-file NewIssue.md \
  --label "type - development" \
  --label "3 story points" \
  --milestone "Top of the backlog"
```

### Common Labels

- `type - development` - New feature or system
- `type - operational` - Maintenance or operational work
- `type - testing & release` - Manual testing and deployment
- `Epic` - Too large for an iteration, needs breakdown
- `Blocked` - Cannot be worked, has blocking dependencies
- `1 story points`, `2 story points`, `3 story points`, etc. - Complexity estimates
- `DataUplift` - the issue is related to Programe of Data Uplift 

### Other Useful Commands

```bash
# List issues
gh issue list

# View an issue
gh issue view <issue-number>

# Add comment
gh issue comment <issue-number> --body "Comment text"
```
