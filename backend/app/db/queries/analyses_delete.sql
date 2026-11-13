-- analyses_delete.sql
delete from analyses where id = %(id)s and user_id = %(user_id)s;