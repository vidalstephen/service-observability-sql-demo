-- Detect client + firmware regressions by comparing the most recent 14 days to the prior 14 days.
WITH bounds AS (
  SELECT MAX(run_date) AS max_date FROM service_runs
), labeled AS (
  SELECT
    r.*,
    CASE
      WHEN r.run_date >= date((SELECT max_date FROM bounds), '-13 day') THEN 'current_14d'
      WHEN r.run_date >= date((SELECT max_date FROM bounds), '-27 day') THEN 'prior_14d'
      ELSE 'older'
    END AS period
  FROM service_runs r
), grouped AS (
  SELECT
    c.client_name,
    firmware_version,
    period,
    COUNT(*) AS runs,
    AVG(accuracy) AS avg_accuracy,
    AVG(delivered_on_time) AS on_time_rate,
    AVG(CASE WHEN issue_category != 'none' THEN 1.0 ELSE 0.0 END) AS issue_rate
  FROM labeled
  JOIN clients c USING (client_id)
  WHERE period IN ('current_14d', 'prior_14d')
  GROUP BY c.client_name, firmware_version, period
), pivoted AS (
  SELECT
    client_name,
    firmware_version,
    SUM(CASE WHEN period='current_14d' THEN runs ELSE 0 END) AS current_runs,
    ROUND(MAX(CASE WHEN period='current_14d' THEN avg_accuracy END), 4) AS current_accuracy,
    ROUND(MAX(CASE WHEN period='prior_14d' THEN avg_accuracy END), 4) AS prior_accuracy,
    ROUND((MAX(CASE WHEN period='current_14d' THEN avg_accuracy END) - MAX(CASE WHEN period='prior_14d' THEN avg_accuracy END)) * 100, 2) AS accuracy_delta_points,
    ROUND((MAX(CASE WHEN period='current_14d' THEN on_time_rate END) - MAX(CASE WHEN period='prior_14d' THEN on_time_rate END)) * 100, 1) AS on_time_delta_points,
    ROUND((MAX(CASE WHEN period='current_14d' THEN issue_rate END) - MAX(CASE WHEN period='prior_14d' THEN issue_rate END)) * 100, 1) AS issue_rate_delta_points
  FROM grouped
  GROUP BY client_name, firmware_version
)
SELECT *,
  CASE
    WHEN accuracy_delta_points <= -2.0 OR on_time_delta_points <= -15 OR issue_rate_delta_points >= 15 THEN 'investigate_now'
    WHEN accuracy_delta_points <= -1.0 OR on_time_delta_points <= -8 OR issue_rate_delta_points >= 8 THEN 'watchlist'
    ELSE 'stable'
  END AS regression_status
FROM pivoted
WHERE current_runs >= 5
ORDER BY
  CASE regression_status WHEN 'investigate_now' THEN 1 WHEN 'watchlist' THEN 2 ELSE 3 END,
  accuracy_delta_points ASC;
