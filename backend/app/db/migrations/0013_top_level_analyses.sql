create view top_level_analyses
with (security_invoker = true) as
select id, user_id, dataset_name, is_sample, row_count, column_count,
       verdict, deciding_checks, engine_version, duration_ms, created_at
from analyses
where parent_id is null;