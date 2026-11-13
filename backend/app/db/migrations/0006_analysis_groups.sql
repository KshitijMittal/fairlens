create table analysis_groups (
  analysis_id    uuid not null references analyses(id) on delete cascade,
  scope          text not null,
  group_label    text not null,
  n              integer not null check (n >= 0),
  positives      integer not null check (positives >= 0),
  selection_rate double precision not null
                   check (selection_rate >= 0 and selection_rate <= 1),
  rate_ci_low    double precision,
  rate_ci_high   double precision,
  tpr            double precision check (tpr is null or tpr between 0 and 1),
  fpr            double precision check (fpr is null or fpr between 0 and 1),
  accuracy       double precision check (accuracy is null or accuracy between 0 and 1),

  primary key (analysis_id, scope, group_label),

  constraint analysis_groups_scope check (scope in ('historical', 'model')),
  constraint analysis_groups_positives check (positives <= n),
  constraint analysis_groups_interval
    check (rate_ci_low is null or rate_ci_high is null
           or rate_ci_low <= rate_ci_high)
);