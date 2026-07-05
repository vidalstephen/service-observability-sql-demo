# Service Observability Handbook

This handbook defines the operating rhythm for service-quality monitoring in the demo.

## Service commitments

| Commitment | Definition | Owner | Review cadence |
|---|---|---|---|
| Accuracy SLA | Percent of scan runs where measured accuracy meets the client contract | Data Science / CV | Daily, weekly rollup |
| Timeliness SLA | Percent of deliverables completed within contracted processing hours | Service Ops | Daily |
| Issue follow-through | Every repeated miss has an owner, status, and verification step | Service Analyst | Twice weekly |
| Capacity readiness | Labeling demand is forecast before contracted workload exceeds staffing | Data Labeling Ops | Weekly |

## Analyst workflow

1. Run the current service-health query.
2. Identify red/yellow clients and compare with prior period.
3. Use regression detection to isolate client + firmware groups.
4. Use root-cause query to identify repeated issue categories.
5. Open or update audit-log entries with owner, severity, and next checkpoint.
6. Verify after mitigation: no issue is closed until the metric improves.

## Escalation rules

| Trigger | Severity | Action |
|---|---|---|
| Accuracy delta <= -2 points | High | Engineering investigation within 1 business day |
| On-time delta <= -15 points | High | Ops queue review same day |
| Issue-rate increase >= 15 points | High | Root-cause review with owner team |
| Backlog rate >= 18% | Medium | Add capacity or reduce queue blockers |
| Any client below 90% SLA attainment | High | Client-success communication draft |

## Documentation standard

Each finding should include:

- metric definition,
- affected client / fleet / firmware / store,
- observed vs expected behavior,
- suspected root cause,
- owner team,
- next action,
- verification query or dashboard link,
- date of next review.
