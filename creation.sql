SET @from_date=DATE_SUB(NOW(), INTERVAL 1 MONTH);
SELECT created_addons.week AS `Week`, created_addons.total AS `Add-ons`,
       created_versions.total AS `Versions`
FROM
  (SELECT WEEK(a.created) AS `week`, COUNT(DISTINCT(a.id)) AS `total`
   FROM versions AS v
   JOIN addons AS a ON (
     v.addon_id = a.id AND a.created >= @from_date AND v.channel = 2 AND
     a.status NOT IN (0,5,11) AND a.addontype_id != 9)
   GROUP BY `week`) AS created_addons
  JOIN
  (SELECT WEEK(v.created) AS `week`, COUNT(*) AS `total`
   FROM versions AS v
   JOIN addons AS a ON (
     v.addon_id = a.id AND v.created >= @from_date AND v.channel = 2 AND
     a.status NOT IN (0,5,11) AND a.addontype_id != 9)
   GROUP BY `week`) AS created_versions
  ON (created_addons.week = created_versions.week);
