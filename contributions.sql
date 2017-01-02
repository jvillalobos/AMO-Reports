SET @from_date=DATE_SUB(NOW(), INTERVAL 7 DAY); SET @to_date=NOW();
SELECT SUM(totals.total) AS 'Total',
       IFNULL(nominations.total, 0) AS '  New',
       IFNULL(updates.total, 0) AS '  Upd',
       IFNULL(super.total, 0) AS '  Adm',
       IFNULL(info.total, 0) AS ' Info',
       REPLACE(totals.display_name, 'Ż', 'Z') AS 'Name'
FROM
  (SELECT u.display_name, COUNT(*) AS `total`, u.id
   FROM log_activity AS l, users AS u
   WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND l.user_id = u.id AND
         l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
         l.created >= @from_date AND l.created < @to_date
   GROUP BY l.user_id) AS `totals`
  LEFT JOIN
    (SELECT COUNT(*) AS `total`, u.id
     FROM log_activity AS l, users AS u
     WHERE l.action IN (21, 42, 43, 22) AND l.user_id = u.id AND
           l.details LIKE '%"reviewtype": "nominated",%' AND
           l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
           l.created >= @from_date AND l.created < @to_date
     GROUP BY l.user_id) AS `nominations`
  ON (totals.id = nominations.id)
  LEFT JOIN
    (SELECT COUNT(*) AS `total`, u.id
     FROM log_activity AS l, users AS u
     WHERE l.action IN (21, 42, 43, 22) AND l.user_id = u.id AND
           l.details LIKE '%"reviewtype": "pending",%' AND
           l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
           l.created >= @from_date AND l.created < @to_date
     GROUP BY l.user_id) AS `updates`
  ON (totals.id = updates.id)
  LEFT JOIN
    (SELECT COUNT(*) AS `total`, u.id
     FROM log_activity AS l, users AS u
     WHERE l.action IN (23,45) AND l.user_id = u.id AND
           l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
           l.created >= @from_date AND l.created < @to_date
     GROUP BY l.user_id) AS `super`
  ON (totals.id = super.id)
  LEFT JOIN
    (SELECT COUNT(*) AS `total`, u.id
     FROM log_activity AS l, users AS u
     WHERE l.action = 44 AND l.user_id = u.id AND
           l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
           l.created >= @from_date AND l.created < @to_date
     GROUP BY l.user_id) AS `info`
  ON (totals.id = info.id)
GROUP BY totals.id
ORDER BY totals.total DESC;
