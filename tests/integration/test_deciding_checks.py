"""The deciding_checks consistency query (BACKEND_SCHEMA 3.3) returns zero rows."""
from app.db import get_pool

CONSISTENCY = """
select a.id
from analyses a
where a.deciding_checks <> case
  when a.verdict = 'pass' then '{}'::text[]
  else (
    select coalesce(array_agg(c.check_code order by c.check_code), '{}')
    from analysis_checks c
    where c.analysis_id = a.id and c.state = a.verdict
  )
end;
"""


def test_deciding_checks_match_the_stored_check_rows(stored):
    verdicts = {
        stored("scholarship.csv")["verdict"],
        stored("loan_approvals.csv")["verdict"],
        stored("hiring_shortlist.csv")["verdict"],
    }
    assert verdicts == {"pass", "fail", "warn"}

    with get_pool().connection() as conn:
        assert conn.execute(CONSISTENCY).fetchall() == []
