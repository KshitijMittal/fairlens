-- users_link_google_sub.sql
update users
set google_sub = %(google_sub)s
where id = %(user_id)s
returning id, email, password_hash, google_sub, display_name, password_changed_at, created_at;
