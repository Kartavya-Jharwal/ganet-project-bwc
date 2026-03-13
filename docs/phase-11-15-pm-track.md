# Phase 11-15 PM Track: Evidence-First System Leadership

## Why This Exists

Claiming infrastructure skill in a README is not enough.
For quant firm project manager roles, this project should show repeatable delivery, engineering coordination, and operational quality through public evidence.

This track positions the owner as:

- a systems program operator,
- an execution-focused technical PM,
- a coordinator of quant workflows and platform reliability,

not as a discretionary quant researcher.

## Positioning Statement

This repository demonstrates how to scope, ship, operate, and communicate a production-like quant monitoring platform with clear artifacts for architecture, CI/CD, observability, and stakeholder reporting.

## Phase 11: Infrastructure Credibility

### Phase 11 Objective

Convert current deployment setup into a public, reproducible, containerized architecture with environment parity.

### Phase 11 Deliverables

- Dockerfile for app worker and web processes.
- docker-compose setup for local parity (app, scheduler, mock services).
- Environment matrix for dev/stage/prod with explicit config boundaries.
- Deployment runbook with rollback steps.

### Phase 11 Public Proof Artifacts

- Dockerfile and docker-compose file in repository root.
- Architecture diagram update in [architecture.md](architecture.md).
- "How to run locally" section with single-command startup.

### Phase 11 Acceptance Criteria

- Fresh clone boots via one compose command.
- Startup health checks pass for all services.
- Rollback procedure documented and tested once.

## Phase 12: CI/CD and Release Discipline

### Phase 12 Objective

Show reliable software delivery practices instead of one-off scripts.

### Phase 12 Deliverables

- Multi-stage CI pipeline: lint, unit tests, integration tests, build validation.
- Branch protection rules and required checks documented.
- Release workflow with semantic version tags and changelog automation.
- Deployment gates for stage then prod.

### Phase 12 Public Proof Artifacts

- Expanded workflows in [.github/workflows](../.github/workflows).
- Release notes template and changelog policy.
- Build and test badges for key workflows.

### Phase 12 Acceptance Criteria

- Every PR requires passing checks before merge.
- Tagged release auto-generates notes and artifact metadata.
- Failed stage deploy blocks prod promote.

## Phase 13: Observability and Ops Readiness

### Phase 13 Objective

Demonstrate the ability to run and monitor the system like an operations owner.

### Phase 13 Deliverables

- Structured logging standard with correlation IDs.
- Metrics for signal cycle latency, feed freshness, cache hit rate, alert success rate.
- Basic alerting policy and on-call severity matrix.
- Incident template and postmortem template.

### Phase 13 Public Proof Artifacts

- Ops dashboard screenshots and metric definitions in docs.
- Incident response playbook and sample postmortem.
- SLO table for core flows.

### Phase 13 Acceptance Criteria

- Mean time to detect tracked for one simulated incident.
- At least one incident drill executed and documented.
- SLO violations can be identified from dashboard data.

## Phase 14: External Validation and Open Source Signal

### Phase 14 Objective

Create external proof that the owner can collaborate across teams and standards.

### Phase 14 Deliverables

- Targeted upstream contributions to 2-3 relevant open-source repos (data tooling, scheduling, or monitoring).
- Public issue discussions showing technical tradeoff communication.
- Reusable internal templates extracted into a small helper package or gist set.

### Phase 14 Public Proof Artifacts

- Linked merged PRs and issue threads.
- "Integration notes" section for what was learned and applied back here.
- Dependency governance notes (why packages were added or replaced).

### Phase 14 Acceptance Criteria

- At least 2 merged external contributions with reviewer interaction.
- At least 1 design decision in this repo references external feedback.
- Contribution log is visible in documentation.

## Phase 15: PM Portfolio Packaging for Quant Firms

### Phase 15 Objective

Translate technical work into hiring-relevant PM evidence.

### Phase 15 Deliverables

- Program charter: problem, scope, constraints, timeline, risks.
- RAID log (Risks, Assumptions, Issues, Dependencies).
- Milestone burndown and delivery metrics.
- Stakeholder update deck style markdown (weekly format).
- Final "operator narrative" document for interviews.

### Phase 15 Public Proof Artifacts

- Portfolio packet folder under docs with reusable templates.
- Executive summary with before/after system maturity table.
- "What I drove" section separating ownership vs individual coding tasks.

### Phase 15 Acceptance Criteria

- A reviewer can evaluate PM capability in 10 minutes from docs alone.
- Every major claim maps to a concrete artifact link.
- Final packet is tailored to quant PM and technical program roles.

## Cross-Phase KPI Scorecard

Track these from Phase 11 through 15:

| KPI | Target | Why It Matters |
| ----- | -------- | ---------------- |
| Deployment reproducibility | 100% fresh boot success in CI sandbox | Proves platform reliability ownership |
| PR lead time | < 2 days median | Shows delivery velocity discipline |
| Change failure rate | < 15% | Demonstrates release quality |
| Incident drill completion | 1 per phase | Proves operational readiness |
| External contribution count | >= 2 merged PRs | Validates collaboration signal |
| Artifact traceability | 1:1 claim-to-evidence mapping | Prevents resume inflation risk |

## Definition of Success

By end of Phase 15, this project should read as a systems delivery case study:

- Designed with architecture intent,
- executed with engineering rigor,
- operated with production discipline,
- communicated with PM clarity.

That is the profile quant firms expect for technical PM and platform program roles.
