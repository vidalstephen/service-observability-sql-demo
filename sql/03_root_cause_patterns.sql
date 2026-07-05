-- Root-cause pattern finder: which issue categories explain missed commitments?
WITH recent AS (
  SELECT *
  FROM service_runs
  WHERE run_date >= (SELECT date(MAX(run_date), '-13 day') FROM service_runs)
), failures AS (
  SELECT
    c.client_name,
    r.store_id,
    r.robot_id,
    r.firmware_version,
    r.issue_category,
    CASE WHEN r.accuracy_met = 0 THEN 1 ELSE 0 END AS missed_accuracy,
    CASE WHEN r.delivered_on_time = 0 THEN 1 ELSE 0 END AS missed_timeliness,
    r.labels_required,
    r.processing_hours
  FROM recent r
  JOIN clients c USING (client_id)
  WHERE r.accuracy_met = 0 OR r.delivered_on_time = 0 OR r.issue_category != 'none'
)
SELECT
  client_name,
  issue_category,
  firmware_version,
  COUNT(*) AS affected_runs,
  SUM(missed_accuracy) AS accuracy_misses,
  SUM(missed_timeliness) AS timeliness_misses,
  ROUND(AVG(labels_required), 0) AS avg_labels_required,
  ROUND(AVG(processing_hours), 1) AS avg_processing_hours,
  GROUP_CONCAT(DISTINCT store_id) AS affected_stores
FROM failures
GROUP BY client_name, issue_category, firmware_version
ORDER BY affected_runs DESC, accuracy_misses DESC, timeliness_misses DESC;
