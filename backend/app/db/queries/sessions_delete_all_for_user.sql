-- sessions_delete_all_for_user.sql
delete from sessions where user_id = %(user_id)s;