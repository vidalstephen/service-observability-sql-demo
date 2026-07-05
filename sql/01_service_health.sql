-- Client and fleet-level service health scorecard for the most recent 14 days.
WITH recent AS (
  SELECT *
  FROM service_runs
  WHERE run_date >= (SELECT date(MAX(run_date), '-13 day') FROM service_runs)
), scored AS (
  SELECT
    c.client_name,
    r.client_id,
    COUNT(*) AS scan_runs,
    ROUND(AVG(r.accuracy), 4) AS avg_accuracy,
    ROUND(AVG(r.accuracy_met) * 100, 1) AS accuracy_sla_attainment_pct,
    ROUND(AVG(r.delivered_on_time) * 100, 1) AS timeliness_sla_attainment_pct,
    ROUND(AVG(r.processing_hours), 1) AS avg_processing_hours,
    c.accuracy_sla,
    c.timeliness_sla_hours,
    SUM(CASE WHEN r.issue_category != 'none' THEN 1 ELSE 0 END) AS issue_count
  FROM recent r
  JOIN clients c USING (client_id)
  GROUP BY r.client_id, c.client_name, c.accuracy_sla, c.timeliness_sla_hours
)
SELECT
  client_name,
  scan_runs,
  avg_accuracy,
  accuracy_sla_attainment_pct,
  timeliness_sla_attainment_pct,
  avg_processing_hours,
  issue_count,
  CASE
    WHEN accuracy_sla_attainment_pct < 90 OR timeliness_sla_attainment_pct < 90 THEN 'red'
    WHEN accuracy_sla_attainment_pct < 95 OR timeliness_sla_attainment_pct < 95 THEN 'yellow'
    ELSE 'green'
  END AS service_status
FROM scored
ORDER BY service_status DESC, accuracy_sla_attainment_pct ASC, timeliness_sla_attainment_pct ASC;
