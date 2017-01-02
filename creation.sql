SET @from_date=DATE_SUB(NOW(), INTERVAL 1 MONTH);
SELECT created_addons.week AS `Week`, created_addons.total AS `Add-ons`,
       created_versions.total AS `Versions`
FROM
  (SELECT WEEK(a.created) AS `week`, COUNT(*) AS `total`
   FROM addons AS a
   WHERE a.is_listed = 1 AND a.created >= @from_date AND
         a.status NOT IN (0,5,11) AND a.addontype_id NOT IN (9, 11)
   GROUP BY `week`) AS created_addons
  JOIN
  (SELECT WEEK(v.created) AS `week`, COUNT(*) AS `total`
   FROM versions AS v
   JOIN addons AS a ON (
     v.addon_id = a.id AND v.created >= @from_date AND a.is_listed = 1 AND
     a.status NOT IN (0,5,11) AND a.addontype_id NOT IN (9, 11))
   GROUP BY `week`) AS created_versions
  ON (created_addons.week = created_versions.week);
