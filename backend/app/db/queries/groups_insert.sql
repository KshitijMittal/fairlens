-- groups_insert.sql
insert into analysis_groups (analysis_id, scope, group_label, n, positives, selection_rate, rate_ci_low, rate_ci_high, tpr, fpr, accuracy)
values (%(analysis_id)s, %(scope)s, %(group_label)s, %(n)s, %(positives)s, %(selection_rate)s, %(rate_ci_low)s, %(rate_ci_high)s, %(tpr)s, %(fpr)s, %(accuracy)s);