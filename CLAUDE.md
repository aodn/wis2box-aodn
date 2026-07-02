# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A WIS 2.0 implementation for the Australian Ocean Data Network (AODN) using wis2box for ocean data management. The active development areas are `wis2-pipeline/`, `docs/`, and `resources/`.

## Directories to IGNORE

Do NOT read, search, index, or modify anything inside the following directories unless the user explicitly asks you to:

- `wis2-terraform/` — infrastructure code, out of scope for this repo's day-to-day work
- `wis2box/` — vendored upstream wis2box code, treated as read-only third-party content

When using search tools (Grep, Glob, `rg`, `find`, etc.), always exclude these two directories from the search scope.
