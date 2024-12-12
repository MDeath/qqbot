from qqbotcls import QQBotSched,bot
from qdb import DataObj

class msglog(DataObj): # 注册数据库
    columns = '''\
id                  INTEGER     PRIMARY KEY     NOT NULL,
time                INTEGER     NOT NULL,
message_id          INTEGER     NOT NULL,
user_id             INTEGER     NOT NULL,
user_name           TEXT        NOT NULL,
user_displayname    TEXT        NOT NULL,
age                 INTEGER     NOT NULL,
group_id            INTEGER     NOT NULL,
target              INTEGER     NOT NULL,
user_remark         TEXT,
gender              INTEGER,
platform            TEXT,
term_type           INTEGER,
sex                 TEXT,
title               TEXT,
title_expire_time   INTEGER,
nickname            TEXT,
card                TEXT,
distance            INTEGER,
honor               TEXT,
join_time           INTEGER,
last_active_time    INTEGER,
last_sent_time      INTEGER,
unique_name         TEXT,
area                TEXT,
level               INTEGER,
role                TEXT,
unfriendly          BLOB,
card_changeable     BLOB,
shut_up_timestamp   INTEGER,
group_name          TEXT,
group_remark        TEXT,
group_uin           INTEGER,
admins              TEXT,
class_text          BLOB,
is_frozen           BLOB,
max_member          INTEGER,
member_num          INTEGER,
member_count        INTEGER,
max_member_count    INTEGER,
message             TEXT
'''

def onPlug(bot):
    bot.db.Add_Tabel_DataObj(msglog)

def onQQMessage(bot, Type, Sender:dict, Source, Message):
    Sender.update(Source, message=Message)
    bot.db.Insert('msglog', Sender)