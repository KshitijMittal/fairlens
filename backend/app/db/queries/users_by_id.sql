-- users_by_id.sql
select id, email, password_hash, google_sub, display_name, password_changed_at, created_at
from users
where id = %(user_id)s;
