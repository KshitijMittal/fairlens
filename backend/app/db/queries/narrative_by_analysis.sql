-- narrative_by_analysis.sql
select analysis_id, kind, body, provider, model_name, created_at
from analysis_narratives
where analysis_id = %(analysis_id)s;