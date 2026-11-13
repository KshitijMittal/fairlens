-- analyses_by_share_token.sql
select a.id, a.user_id, a.parent_id, a.repair_strategy, a.dataset_name, a.source_sha256,
       a.is_sample, a.sample_slug, a.row_count, a.column_count, a.columns,
       a.outcome_column, a.positive_value, a.group_column, a.group_count, a.age_banding,
       a.sampling, a.thresholds, a.model_card, a.encoding, a.proxies,
       a.verdict, a.deciding_checks, a.seed, a.engine_version, a.duration_ms, a.created_at
from analyses a
join shares s on s.analysis_id = a.id
where s.token_hash = %(token_hash)s;