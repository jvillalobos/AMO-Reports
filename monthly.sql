SET @from_date=STR_TO_DATE(CONCAT(EXTRACT(YEAR_MONTH FROM NOW()), "01"),"%Y%m%d"); SET @to_date=DATE_ADD(@from_date, INTERVAL 1 MONTH);
SELECT IFNULL(COUNT(*), 0)
FROM log_activity AS l
WHERE l.action IN (21, 42, 43, 22, 23, 44, 45, 144, 147, 148) AND
      l.arguments LIKE '%"addons.addon"%' AND l.user_id != 4757633 AND
      l.created >=  @from_date AND l.created < @to_date;
