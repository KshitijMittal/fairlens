create or replace function reject_metric_update() returns trigger
language plpgsql as $$
begin
  raise exception
    'fairlens: % is immutable; delete the analysis and run it again', tg_table_name
    using errcode = 'restrict_violation';
end;
$$;

create trigger analyses_immutable
  before update on analyses
  for each row execute function reject_metric_update();

create trigger analysis_checks_immutable
  before update on analysis_checks
  for each row execute function reject_metric_update();

create trigger analysis_groups_immutable
  before update on analysis_groups
  for each row execute function reject_metric_update();

create trigger analysis_repairs_immutable
  before update on analysis_repairs
  for each row execute function reject_metric_update();