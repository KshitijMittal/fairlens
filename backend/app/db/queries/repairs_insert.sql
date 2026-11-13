-- repairs_insert.sql
insert into analysis_repairs (
    analysis_id, strategy, changed_rows, changed_columns, dropped_columns,
    parity_after, amplification_after, tpr_gap_after, accuracy_after,
    verdict_after, recommended, summary
) values (
    %(analysis_id)s, %(strategy)s, %(changed_rows)s, %(changed_columns)s, %(dropped_columns)s,
    %(parity_after)s, %(amplification_after)s, %(tpr_gap_after)s, %(accuracy_after)s,
    %(verdict_after)s, %(recommended)s, %(summary)s
)
returning analysis_id, strategy, changed_rows, changed_columns, dropped_columns,
        parity_after, amplification_after, tpr_gap_after, accuracy_after,
        verdict_after, recommended, summary, created_at;