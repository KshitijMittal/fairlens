-- checks_by_analysis.sql
select analysis_id, check_code, state, value, ci_low, ci_high, threshold, reason
from analysis_checks
where analysis_id = %(analysis_id)s
order by check_code;