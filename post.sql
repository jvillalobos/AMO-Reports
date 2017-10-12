SELECT
  CASE WHEN ea.weight > 150  THEN "highest"
       WHEN ea.weight > 100  THEN "high"
       WHEN ea.weight >  20  THEN "medium"
       ELSE "low" END AS `risk_level`,
 COUNT(*)
FROM addons AS a
JOIN versions AS v ON (a.current_version = v.id)
JOIN editors_autoapprovalsummary AS ea ON (v.id = ea.version_id)
JOIN addons_addonapprovalscounter AS aa
  ON (a.id = aa.addon_id AND
    ((aa.last_human_review IS NULL) OR (aa.last_human_review < ea.created)))
WHERE a.status = 4 AND a.inactive = 0
GROUP BY `risk_level`;
