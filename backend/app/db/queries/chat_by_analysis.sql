-- chat_by_analysis.sql
select id, analysis_id, role, body, citations, created_at
from chat_messages
where analysis_id = %(analysis_id)s
order by created_at;