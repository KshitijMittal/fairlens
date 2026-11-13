-- narrative_insert.sql
insert into analysis_narratives (analysis_id, kind, body, provider, model_name)
values (%(analysis_id)s, %(kind)s, %(body)s, %(provider)s, %(model_name)s)
returning analysis_id, kind, body, provider, model_name, created_at;