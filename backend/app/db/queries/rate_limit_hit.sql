-- rate_limit_hit.sql
insert into rate_limits (bucket, identifier, window_start, count)
values (%(bucket)s, %(identifier)s, date_trunc('hour', now()), 1)
on conflict (bucket, identifier, window_start)
do update set count = rate_limits.count + 1
returning count;