SET @from_date=DATE_SUB(NOW(), INTERVAL 7 DAY); SET @to_date=NOW();
SELECT all.total AS `Total`, community.total AS `Community`,
       automatic.total AS `Auto` FROM
  (SELECT COUNT(*) AS `total`
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22, 23, 44, 45, 144, 147, 148) AND
         l.arguments LIKE '%"addons.addon"%' AND
         l.created >= @from_date AND l.created < @to_date) AS `all`
  JOIN
  (SELECT COUNT(*) AS `total`
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22, 23, 44, 45, 144, 147, 148) AND
         l.arguments LIKE '%"addons.addon"%' AND
         l.created >= @from_date AND l.created < @to_date AND
         l.user_id NOT IN (
           SELECT DISTINCT(gu.user_id) FROM groups_users AS gu
           WHERE gu.group_id = 50066)) AS `community`
  JOIN
  (SELECT COUNT(*) AS `total`
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22, 23, 44, 45, 144, 147, 148) AND
         l.user_id = 4757633 AND l.arguments LIKE '%"addons.addon"%' AND
         l.created >= @from_date AND l.created < @to_date) AS `automatic`;
