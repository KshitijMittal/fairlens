-- repairs_by_analysis.sql
select analysis_id, strategy, changed_rows, changed_columns, dropped_columns,
       parity_after, amplification_after, tpr_gap_after, accuracy_after,
       verdict_after, recommended, summary, created_at
from analysis_repairs
where analysis_id = %(analysis_id)s
order by strategy;