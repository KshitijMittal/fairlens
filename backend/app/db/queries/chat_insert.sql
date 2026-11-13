-- chat_insert.sql
insert into chat_messages (analysis_id, role, body, citations)
values (%(analysis_id)s, %(role)s, %(body)s, %(citations)s)
returning id, analysis_id, role, body, citations, created_at;