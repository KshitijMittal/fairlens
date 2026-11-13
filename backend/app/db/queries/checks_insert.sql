-- checks_insert.sql
insert into analysis_checks (analysis_id, check_code, state, value, ci_low, ci_high, threshold, reason)
values (%(analysis_id)s, %(check_code)s, %(state)s, %(value)s, %(ci_low)s, %(ci_high)s, %(threshold)s, %(reason)s);