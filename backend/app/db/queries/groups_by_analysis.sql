-- groups_by_analysis.sql
select analysis_id, scope, group_label, n, positives, selection_rate,
       rate_ci_low, rate_ci_high, tpr, fpr, accuracy
from analysis_groups
where analysis_id = %(analysis_id)s
order by scope, group_label;