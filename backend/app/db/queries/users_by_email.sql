-- users_by_email.sql
select id, email, password_hash, google_sub, display_name, password_changed_at, created_at
from users
where lower(email) = lower(%(email)s);