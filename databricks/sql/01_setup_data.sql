-- ============================================================================
-- Better2gether Care Copilot — Data Foundation Setup
-- Run this in a Databricks SQL editor or notebook (SQL) on a Serverless warehouse.
--
-- EDIT THESE if you want a different catalog/schema:
--   catalog = main            (any Unity Catalog you can write to)
--   schema  = care_copilot
-- Find/replace `better2gether.care_copilot` throughout if you change them.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS better2gether.care_copilot;

-- ----------------------------------------------------------------------------
-- 1) device_registry — one row per wearable device (the device dimension)
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE better2gether.care_copilot.device_registry
COMMENT 'Device dimension: one row per Better2gether smartwatch. Join to vitals_alerts on device_id.'
AS
WITH nums AS (SELECT explode(sequence(1, 20)) AS n)
SELECT
  concat('watch-', lpad(cast(n AS string), 3, '0'))                                          AS device_id,
  concat('MBR-', lpad(cast(n AS string), 5, '0'))                                            AS member_id,
  element_at(array('B2G Pulse','B2G Pulse Pro','B2G Vital'), cast(pmod(n,3) AS int)+1)        AS model,
  date_add(DATE'2026-01-01', cast(pmod(n*7,120) AS int))                                      AS enrollment_date,
  element_at(array('NYC-Metro','Long Island','Hudson Valley','New Jersey','Connecticut'),
             cast(pmod(n,5) AS int)+1)                                                        AS region,
  element_at(array('Basic','Plus','Premium'), cast(pmod(n,3) AS int)+1)                       AS plan_tier,
  element_at(array('18-29','30-44','45-59','60-74'), cast(pmod(n,4) AS int)+1)                AS age_band,
  CASE WHEN n <= 5 THEN 'v2.3.8' ELSE 'v2.4.1' END                                            AS firmware_version
FROM nums;

-- ----------------------------------------------------------------------------
-- 2) vitals_alerts — derived alert events (the fact table)
--    Alert codes MUST match the Knowledge Base docs exactly.
--    watch-007 is seeded rich (9 SPO2-CRIT / 13 SPO2-LOW) for the demo money-shot.
--    watch-001..005 are on legacy firmware v2.3.8 with extra battery alerts.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE TABLE better2gether.care_copilot.vitals_alerts
COMMENT 'Vitals alert events. alert_code in (SPO2-CRIT, SPO2-LOW, HR-HIGH, TEMP-HIGH, BATT-LOW, BATT-CRIT).'
AS
WITH codes AS (
  SELECT * FROM VALUES
    ('SPO2-CRIT','High',   93.5, 'Blood oxygen dropped below 94.3% - flag for follow-up', 9),
    ('SPO2-LOW', 'Medium', 94.6, 'Blood oxygen below 95% - monitor',                      16),
    ('HR-HIGH',  'Medium', 158.0,'Elevated heart rate while at rest or asleep',           14),
    ('TEMP-HIGH','Low',    37.4, 'Skin temperature at or above 37.3C',                    14),
    ('BATT-LOW', 'Low',    12.0, 'Battery low below 15%',                                 11),
    ('BATT-CRIT','Medium', 6.0,  'Battery critically low below 8%',                        5)
  AS t(alert_code, severity, metric_value, description, base_cnt)
),
devs AS (
  SELECT device_id, CAST(regexp_extract(device_id, '([0-9]+)', 1) AS INT) AS n
  FROM better2gether.care_copilot.device_registry
),
expanded AS (
  SELECT d.device_id, d.n, c.alert_code, c.severity, c.metric_value, c.description,
    explode(sequence(1,
      CASE
        WHEN c.alert_code LIKE 'BATT%' AND d.n <= 5           THEN c.base_cnt + 8   -- legacy fw = more battery alerts
        WHEN c.alert_code = 'SPO2-CRIT' AND d.n = 7           THEN 9                -- money-shot device
        WHEN c.alert_code = 'SPO2-LOW'  AND d.n = 7           THEN 13
        ELSE greatest(1, cast(pmod(d.n*3 + length(c.alert_code), 7) AS int) + 1)
      END)) AS i
  FROM devs d CROSS JOIN codes c
)
SELECT
  concat('ALT-', lpad(cast(row_number() OVER (ORDER BY device_id, alert_code, i) AS string), 6, '0')) AS alert_id,
  device_id,
  timestampadd(MINUTE, -cast(i*17 AS int), TIMESTAMP'2026-07-05 12:00:00')                             AS alert_time,
  alert_code,
  severity,
  round(metric_value + pmod(i,3)*0.1, 1)                                                               AS metric_value,
  description
FROM expanded;

-- ----------------------------------------------------------------------------
-- 3) Volume for the Knowledge Assistant source documents
-- ----------------------------------------------------------------------------
CREATE VOLUME IF NOT EXISTS better2gether.care_copilot.care_kb;

-- ----------------------------------------------------------------------------
-- Sanity checks
-- ----------------------------------------------------------------------------
SELECT 'device_registry' AS tbl, count(*) AS rows FROM better2gether.care_copilot.device_registry
UNION ALL
SELECT 'vitals_alerts',           count(*)        FROM better2gether.care_copilot.vitals_alerts;

-- Expect ~629 alerts across 6 codes; watch-007 has 9 SPO2-CRIT / 13 SPO2-LOW.
SELECT alert_code, count(*) AS cnt
FROM better2gether.care_copilot.vitals_alerts
GROUP BY alert_code ORDER BY cnt DESC;
