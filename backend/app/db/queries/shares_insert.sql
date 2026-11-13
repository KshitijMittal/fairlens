-- shares_insert.sql
insert into shares (token_hash, analysis_id)
values (%(token_hash)s, %(analysis_id)s)
returning token_hash, analysis_id, created_at, last_viewed_at, view_count;