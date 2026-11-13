-- analyses_for_user.sql
-- Reads from top_level_analyses view to keep repair children nested
select
  id, user_id, dataset_name, is_sample, row_count, column_count,
  verdict, deciding_checks, engine_version, duration_ms, created_at
from top_level_analyses
where user_id = %(user_id)s
order by created_at desc
limit %(limit)s offset %(offset)s;