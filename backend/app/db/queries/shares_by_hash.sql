-- shares_by_hash.sql
select token_hash, analysis_id, created_at, last_viewed_at, view_count
from shares
where token_hash = %(token_hash)s;