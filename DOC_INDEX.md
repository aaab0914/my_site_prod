# Documentation Index

This file is the main index for project documentation in `my_site_prod-master`.

Project root:

```text
G:\Projests\Python_Projects\my_site_prod-master
```

## Start Here

- `README.md`
  Main project overview, startup, deployment basics, troubleshooting, backup and restore.

- `DOC_INDEX.md`
  This file. Use it as the top-level documentation entry.

## Deployment And Operations

- `PRODUCTION_VERIFICATION.md`
  Production deployment verification checklist for real server use.

- `PROJECT_OPERATIONS_GUIDE.md`
  Combined operations guide covering PostgreSQL, Django shell, Docker Compose, and observability operations.

- `OBSERVABILITY_RUNBOOK.md`
  Focused runbook for Celery, Sentry, Prometheus, Grafana, Flower, metrics checks, and common recovery steps.

- `PSQL_GUIDE.md`
  Project-specific PostgreSQL `psql` operations.

- `DJANGO_SHELL_GUIDE.md`
  Project-specific Django shell operations.

- `DOCKER_GUIDE.md`
  Project-specific Docker Compose operations.

- `SHELL_GUIDE.md`
  General PowerShell and shell-style file/log/query operations for this project.

- `GIT_GUIDE.md`
  Local Git operations for this repository.

- `GITHUB_GUIDE.md`
  GitHub CLI and remote workflow operations, if this repo is connected to GitHub.

## Testing

- `TEST_INDEX.md`
  Full list of test files, test paths, and recommended run commands.

- `SOURCE_STRUCTURE.md`
  Current Python package layout after views/forms/models/tests/admin/urls were reorganized into package directories.

- `INTEGRATIONS_GUIDE.md`
  Runtime integration guide for Celery, Sentry, Prometheus, Grafana, Flower, Redis, and Elasticsearch.

## Stabilization And Risk Tracking

- `STABILIZATION_CHECKLIST.md`
  Main stabilization checklist and recommended sequencing.

- `REMAINING_ISSUES_PRIORITY.md`
  Current priority list for unresolved project issues.

- `MIDDLEWARE_MIGRATION_PLAN.md`
  Notes on moving away from heavy login middleware control.

## Route And Access Policy

- `ROUTE_ACCESS_POLICY.md`
  Public/private/admin route policy summary.

- `ROUTE_ACCESS_AUDIT.md`
  Route access audit notes for the current project.

## Other Existing Docs

- `API_DOCUMENTATION.md`
  API-related documentation already present in the repository.

- `RUNTIME_ARTIFACTS.md`
  Runtime-generated directories and handling notes for `data/`, `media/`, `staticfiles/`, `logs/`, and `backups/`.

- `README_EN.md`
  English README variant already present in the repository.

- `CLAUDE.md`
  Existing repository-level notes file already present in the repository.

## Recommended Reading Order

1. `README.md`
2. `DOC_INDEX.md`
3. `INTEGRATIONS_GUIDE.md`
4. `OBSERVABILITY_RUNBOOK.md`
5. `TEST_INDEX.md`
6. `PRODUCTION_VERIFICATION.md`
7. `STABILIZATION_CHECKLIST.md`
6. Then open one of:
   `PSQL_GUIDE.md`, `DJANGO_SHELL_GUIDE.md`, `DOCKER_GUIDE.md`, `SHELL_GUIDE.md`, `GIT_GUIDE.md`, `GITHUB_GUIDE.md`

## Suggested Daily Use

- For startup or deployment: `README.md`, `PRODUCTION_VERIFICATION.md`, `DOCKER_GUIDE.md`
- For observability and recovery: `INTEGRATIONS_GUIDE.md`, `OBSERVABILITY_RUNBOOK.md`, `PROJECT_OPERATIONS_GUIDE.md`
- For tests: `TEST_INDEX.md`
- For database inspection: `PSQL_GUIDE.md`
- For Django ORM inspection: `DJANGO_SHELL_GUIDE.md`
- For local terminal operations: `SHELL_GUIDE.md`
- For version control: `GIT_GUIDE.md`, `GITHUB_GUIDE.md`
