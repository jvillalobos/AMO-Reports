SELECT SUM(rs.score) AS 'Total',
       CASE WHEN SUM(rs.score) >= 3000000  THEN '9'
            WHEN SUM(rs.score) >= 1200000  THEN '8'
            WHEN SUM(rs.score) >=  300000  THEN '7'
            WHEN SUM(rs.score) >=   96000  THEN '6'
            WHEN SUM(rs.score) >=   45000  THEN '5'
            WHEN SUM(rs.score) >=   21000  THEN '4'
            WHEN SUM(rs.score) >=    8700  THEN '3'
            WHEN SUM(rs.score) >=    4320  THEN '2'
            WHEN SUM(rs.score) >=    2160  THEN '1'
            ELSE '0' END AS '  Level',
       REPLACE(u.display_name, 'Ż', 'Z') AS 'Name'
FROM reviewer_scores AS rs
INNER JOIN users AS u ON (rs.user_id = u.id)
INNER JOIN groups_users AS gu
  ON (gu.group_id = 50002 AND u.id = gu.user_id AND
      u.id NOT IN (
        SELECT gu2.user_id FROM groups_users AS gu2
        WHERE gu2.group_id IN (50000, 50066)))
GROUP BY rs.user_id
ORDER BY SUM(rs.score) DESC;
