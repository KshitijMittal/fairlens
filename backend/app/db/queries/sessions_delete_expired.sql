-- sessions_delete_expired.sql
delete from sessions where expires_at < now();