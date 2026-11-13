-- llm_cache_put.sql
insert into llm_cache (key_hash, analysis_id, kind, prompt_version, response)
values (%(key_hash)s, %(analysis_id)s, %(kind)s, %(prompt_version)s, %(response)s)
on conflict (key_hash) do update set response = excluded.response
returning key_hash, analysis_id, kind, prompt_version, response, created_at;