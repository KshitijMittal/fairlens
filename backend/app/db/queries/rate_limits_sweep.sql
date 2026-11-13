-- rate_limits_sweep.sql
delete from rate_limits where window_start < now() - interval '1 day';