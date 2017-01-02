SELECT unlisted_we.total AS `Unlisted`, listed_we.total AS `Listed`,
       listed_we.adi AS `Listed ADI`
FROM
  (SELECT COUNT(DISTINCT(a.id)) AS `total`
   FROM files AS f
   JOIN versions AS v ON (
     f.version_id = v.id AND f.is_webextension = 1 AND f.status = 4)
   JOIN addons AS a ON (
     v.addon_id = a.id AND a.status != 5 AND a.inactive = 0 AND
     a.addontype_id = 1 AND a.is_listed = 0)) AS `unlisted_we`,
  (SELECT COUNT(*) AS `total`, SUM(WebExt.users) AS `adi` FROM
    (SELECT a.id, a.average_daily_users AS `users`
     FROM files AS f
     JOIN versions AS v ON (
       f.version_id = v.id AND f.is_webextension = 1 AND f.status = 4)
     JOIN addons AS a ON (
       v.addon_id = a.id AND a.status = 4 AND a.inactive = 0 AND
       a.addontype_id = 1 AND a.is_listed = 1)
     GROUP BY a.id) AS `WebExt`) AS `listed_we`;
