SELECT unlisted_we.total AS `Unlisted`, listed_we.total AS `Listed`,
       listed_we.adi AS `Listed ADI`
FROM
  (SELECT COUNT(DISTINCT(a.id)) AS `total`
   FROM files AS f
   JOIN versions AS v ON (
     f.version_id = v.id AND f.is_webextension = 1 AND f.status = 4 AND
     v.channel = 1)
   JOIN addons AS a ON (
     v.addon_id = a.id AND a.status NOT IN (5, 11) AND a.inactive = 0 AND
     a.addontype_id = 1)) AS `unlisted_we`,
  (SELECT COUNT(*) AS `total`, SUM(WebExt.users) AS `adi` FROM
    (SELECT DISTINCT(a.id), a.average_daily_users AS `users`
     FROM files AS f
     JOIN versions AS v ON (
       f.version_id = v.id AND f.is_webextension = 1 AND f.status = 4 AND
       v.channel = 2)
     JOIN addons AS a ON (
       v.addon_id = a.id AND a.status = 4 AND a.inactive = 0 AND
       a.addontype_id = 1)
     GROUP BY a.id) AS `WebExt`) AS `listed_we`;
