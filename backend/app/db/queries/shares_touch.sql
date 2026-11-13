-- shares_touch.sql
update shares
set last_viewed_at = now(), view_count = view_count + 1
where token_hash = %(token_hash)s
returning token_hash, analysis_id, created_at, last_viewed_at, view_count;