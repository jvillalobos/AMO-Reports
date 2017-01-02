SET @from_date=DATE_SUB(NOW(), INTERVAL 7 DAY); SET @to_date=NOW();
SELECT times.review_time AS `Waiting`, COUNT(*) AS `Total`
FROM
  (SELECT f.version_id,
    CASE
      WHEN DATE_SUB(f.reviewed, INTERVAL 5 DAY) < MIN(f.created) THEN "0-5 days"
      WHEN DATE_SUB(f.reviewed, INTERVAL 10 DAY) < MIN(f.created) THEN "5-10 days"
      ELSE "More than 10 days"
      END AS `review_time`
   FROM files AS f
   WHERE f.reviewed >= @from_date AND f.reviewed < @to_date
   GROUP BY f.version_id) AS `times`
  JOIN versions AS v ON (times.version_id = v.id)
  JOIN addons AS a ON (v.addon_id = a.id AND  a.is_listed = 1)
GROUP BY times.review_time;
