-- analyses_owner.sql
-- Kept apart from analyses_by_id so the result payload never has to carry user_id.
select user_id
from analyses
where id = %(id)s;
