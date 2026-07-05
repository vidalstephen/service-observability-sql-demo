# Issue Audit Log Template

| Field | Example |
|---|---|
| Issue ID | `ISS-2026-001` |
| Opened | `2026-07-05` |
| Client / Fleet | `FreshBasket / firmware 4.9.0` |
| Metric impacted | `Accuracy SLA` |
| Severity | `High` |
| Symptom | `Accuracy down 2.8 percentage points vs prior 14 days` |
| Suspected root cause | `camera_blur` |
| Owner team | `Computer Vision` |
| Next action | `Review image-quality distribution and firmware rollout cohort` |
| Verification method | Re-run `sql/02_regression_detection.sql` after patch deployment |
| Status | `investigating` |
| Next checkpoint | `2026-07-08` |

## Close criteria

An issue can be closed only when:

1. the responsible team has shipped or documented the mitigation,
2. the affected metric recovered or the exception was accepted,
3. the report/dashboard was re-run,
4. the owner and verification date are recorded.
