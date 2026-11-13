-- analyses_by_id.sql
-- The stored AnalysisResult, exactly as it was returned when the run finished.
select result
from analyses
where id = %(id)s;
