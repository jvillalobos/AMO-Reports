SET @from_date=DATE_SUB(NOW(), INTERVAL 7 DAY); SET @to_date=NOW();
SELECT COUNT(*) AS 'Total',
       u.id IN
         (SELECT gu.user_id FROM groups_users AS gu WHERE gu.group_id = "50000")
       AS `Admin`,
       REPLACE(u.display_name, 'Ż', 'Z') AS 'Name'

FROM log_activity AS l, users AS u
WHERE l.action IN (21, 42, 43, 22, 23, 44, 45, 144) AND l.user_id = u.id AND
      l.user_id != 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
      l.created >= @from_date AND l.created < @to_date
GROUP BY u.id
ORDER BY `Total` DESC;
