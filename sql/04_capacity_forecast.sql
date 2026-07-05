-- Simple labeling capacity forecast: estimate next-week labor need from recent volume and issue mix.
WITH recent AS (
  SELECT *
  FROM service_runs
  WHERE run_date >= (SELECT date(MAX(run_date), '-13 day') FROM service_runs)
), client_volume AS (
  SELECT
    c.client_name,
    COUNT(*) / 2.0 AS avg_weekly_runs,
    AVG(labels_required) AS avg_labels_per_run,
    AVG(CASE WHEN issue_category = 'labeling_backlog' THEN 1.0 ELSE 0.0 END) AS backlog_rate,
    c.contracted_weekly_scans
  FROM recent r
  JOIN clients c USING (client_id)
  GROUP BY c.client_name, c.contracted_weekly_scans
)
SELECT
  client_name,
  ROUND(avg_weekly_runs, 1) AS observed_weekly_runs,
  contracted_weekly_scans,
  ROUND(avg_labels_per_run, 0) AS avg_labels_per_run,
  ROUND(backlog_rate * 100, 1) AS backlog_rate_pct,
  ROUND(MAX(avg_weekly_runs, contracted_weekly_scans) * 1.10, 1) AS forecast_runs_next_week,
  ROUND(MAX(avg_weekly_runs, contracted_weekly_scans) * 1.10 * avg_labels_per_run, 0) AS forecast_labels_next_week,
  ROUND((MAX(avg_weekly_runs, contracted_weekly_scans) * 1.10 * avg_labels_per_run) / 900.0, 1) AS estimated_labeler_days,
  CASE
    WHEN backlog_rate >= 0.18 THEN 'add_capacity_and_review_queue_health'
    WHEN backlog_rate >= 0.10 THEN 'watch_capacity'
    ELSE 'capacity_ok'
  END AS capacity_recommendation
FROM client_volume
ORDER BY estimated_labeler_days DESC;
