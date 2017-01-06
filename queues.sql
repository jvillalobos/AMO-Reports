SELECT queues.waiting, COUNT(IF(queues.status = 3, 1, NULL)) AS `New`,
       COUNT(IF(queues.status = 4, 1, NULL)) AS `Updates`
FROM
  (SELECT a.id, a.status,
    CASE
      WHEN DATE_ADD(MAX(f.created), INTERVAL 5 DAY) > NOW() THEN "green"
      WHEN DATE_ADD(MAX(f.created), INTERVAL 10 DAY) > NOW() THEN "yellow"
      ELSE "red"
      END AS `waiting`
  FROM files AS f
  JOIN versions AS v ON (f.status = 1 AND f.version_id = v.id)
  JOIN addons AS a ON
    (a.status IN (3,4) AND v.addon_id = a.id AND a.inactive = 0 AND
     a.is_listed = 1)
  GROUP BY a.id) AS `queues`
GROUP BY queues.waiting;
