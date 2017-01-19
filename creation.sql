SET @from_date=DATE_SUB(NOW(), INTERVAL 7 DAY); SET @to_date=NOW();
SELECT created_addons.total AS `Add-ons`, created_versions.total AS `Versions`
FROM
  (SELECT COUNT(DISTINCT(a.id)) AS `total`
   FROM versions AS v
   JOIN addons AS a ON (v.addon_id = a.id)
   WHERE a.created >= @from_date AND a.created < @to_date AND v.channel = 2 AND
         a.status NOT IN (0,5,11) AND a.addontype_id != 9
   ) AS created_addons,
  (SELECT COUNT(DISTINCT(v.id)) AS `total`
   FROM versions AS v
   JOIN addons AS a ON (v.addon_id = a.id)
   WHERE v.created >= @from_date AND v.created < @to_date AND v.channel = 2 AND
         a.status NOT IN (0,5,11) AND a.addontype_id != 9
   ) AS created_versions;
