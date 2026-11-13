create table rate_limits (
  bucket       text not null,
  identifier   text not null,
  window_start timestamptz not null,
  count        integer not null default 0 check (count >= 0),

  primary key (bucket, identifier, window_start)
);

create index rate_limits_window_idx on rate_limits (window_start);