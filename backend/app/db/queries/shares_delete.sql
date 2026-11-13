-- shares_delete.sql
delete from shares where token_hash = %(token_hash)s;