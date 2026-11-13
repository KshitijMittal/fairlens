-- account_export_counts.sql
select
  (select count(*) from sessions            where user_id = %(user_id)s) as sessions,
  (select count(*) from auth_tokens         where user_id = %(user_id)s) as tokens,
  (select count(*) from analyses            where user_id = %(user_id)s) as analyses,
  (select count(*) from analysis_checks     where analysis_id in (select id from analyses where user_id = %(user_id)s)) as checks,
  (select count(*) from analysis_groups     where analysis_id in (select id from analyses where user_id = %(user_id)s)) as groups,
  (select count(*) from analysis_narratives where analysis_id in (select id from analyses where user_id = %(user_id)s)) as narratives,
  (select count(*) from analysis_repairs    where analysis_id in (select id from analyses where user_id = %(user_id)s)) as repairs,
  (select count(*) from chat_messages       where analysis_id in (select id from analyses where user_id = %(user_id)s)) as chats,
  (select count(*) from shares              where analysis_id in (select id from analyses where user_id = %(user_id)s)) as shares,
  (select count(*) from llm_cache           where analysis_id in (select id from analyses where user_id = %(user_id)s)) as cache;