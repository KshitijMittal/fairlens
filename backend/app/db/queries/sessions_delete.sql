-- sessions_delete.sql
delete from sessions where token_hash = %(token_hash)s;