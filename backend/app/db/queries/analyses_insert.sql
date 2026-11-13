-- analyses_insert.sql
-- One row: the analysis, with the exact AnalysisResult it produced.
-- Parametrised from the engine payload by Repository.create_analysis.

insert into analyses (
    id, user_id, parent_id, repair_strategy, dataset_name, source_sha256,
    is_sample, sample_slug, row_count, column_count, columns,
    outcome_column, positive_value, group_column, group_count, age_banding,
    sampling, thresholds, model_card, encoding, proxies, result,
    verdict, deciding_checks, seed, engine_version, duration_ms
) values (
    %(id)s, %(user_id)s, %(parent_id)s, %(repair_strategy)s, %(dataset_name)s, %(source_sha256)s,
    %(is_sample)s, %(sample_slug)s, %(row_count)s, %(column_count)s, %(columns)s,
    %(outcome_column)s, %(positive_value)s, %(group_column)s, %(group_count)s, %(age_banding)s,
    %(sampling)s, %(thresholds)s, %(model_card)s, %(encoding)s, %(proxies)s, %(result)s,
    %(verdict)s, %(deciding_checks)s, %(seed)s, %(engine_version)s, %(duration_ms)s
)
returning id;
