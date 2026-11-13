-- users_by_google_sub.sql
select id, email, password_hash, google_sub, display_name, password_changed_at, created_at
from users
where google_sub = %(google_sub)s;