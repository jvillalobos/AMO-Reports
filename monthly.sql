SET @from_date=STR_TO_DATE(CONCAT(EXTRACT(YEAR_MONTH FROM NOW()), "01"),"%Y%m%d"); SET @to_date=DATE_ADD(@from_date, INTERVAL 1 MONTH);
SELECT
  (SELECT IFNULL(COUNT(*), 0)
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22) AND
         l.arguments LIKE '%"addons.addon"%' AND
         l.details LIKE '%"reviewtype": "nominated",%' AND
         l.user_id != 4757633 AND l.created >= @from_date AND
         l.created < @to_date) As 'New Add-ons',
  (SELECT IFNULL(COUNT(*), 0)
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22) AND
         l.arguments LIKE '%"addons.addon"%' AND
         l.details LIKE '%"reviewtype": "pending",%' AND
         l.user_id != 4757633 AND l.created >=  @from_date AND
         l.created < @to_date) AS 'Updates',
  (SELECT IFNULL(COUNT(*), 0)
   FROM log_activity AS l
   WHERE l.action IN (23,45) AND l.arguments LIKE '%"addons.addon"%' AND
         l.user_id != 4757633 AND l.created >=  @from_date AND
         l.created < @to_date) AS 'Admin Review',
  (SELECT IFNULL(COUNT(*), 0)
   FROM log_activity AS l
   WHERE l.action = 44 AND l.arguments LIKE '%"addons.addon"%' AND
         l.user_id != 4757633 AND l.created >=  @from_date AND
         l.created < @to_date) AS 'Info Request',
  (SELECT IFNULL(COUNT(*), 0)
   FROM log_activity AS l
   WHERE l.action IN (21, 42, 43, 22, 23, 44, 45) AND
         l.arguments LIKE '%"addons.addon"%' AND l.user_id != 4757633 AND
         l.created >=  @from_date AND l.created < @to_date) AS 'Total';
