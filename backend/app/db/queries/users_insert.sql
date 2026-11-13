-- users_insert.sql
insert into users (email, password_hash, google_sub, display_name)
values (%(email)s, %(password_hash)s, %(google_sub)s, %(display_name)s)
returning id, email, password_hash, google_sub, display_name, password_changed_at, created_at;