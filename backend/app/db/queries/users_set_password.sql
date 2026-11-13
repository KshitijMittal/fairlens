-- users_set_password.sql
update users
set password_hash = %(password_hash)s,
    password_changed_at = now()
where id = %(user_id)s
returning id, email, password_hash, google_sub, display_name, password_changed_at, created_at;