-- llm_cache_get.sql
select key_hash, analysis_id, kind, prompt_version, response, created_at
from llm_cache
where key_hash = %(key_hash)s;