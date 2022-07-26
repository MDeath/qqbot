# -*- coding: utf-8 -*-

import sqlite3, traceback

class QContact(object):
    def __init__(self, *fields):
        for k, field in zip(self.fields, fields):
            self.__dict__[k] = field
        self.__dict__['ctype'] = self.__class__.ctype

    def __repr__(self):
        return '%s“%s”' % (self.chs_type, self.name)

    def __setattr__(self, k, v):
        raise TypeError("QContact object is readonly")

class Friend(QContact):
    columns = '''\
        qq VARCHAR(12) PRIMARY KEY,
        name VARCHAR(80),
        mark VARCHAR(80),
        power INTEGER(1)
    '''

class Group(QContact):
    columns = '''\
        qq VARCHAR(12) PRIMARY KEY,
        name VARCHAR(80),
        permission VARCHAR(10)
    '''

class GroupMember(QContact):
    columns = '''\
        qq VARCHAR(12) PRIMARY KEY,
        name VARCHAR(80),
        permission  VARCHAR(10)
        card VARCHAR(80),
        joinTime INTEGER,
        lastSpeakTime INTEGER,
        muteTime INTEGER
    '''

CTYPES = {
    'friend': '好友', 'group': '群', 'groupmember': '成员'
}

contactMaker = {}

for cls in [Friend, Group, GroupMember]:
    cls.ctype = cls.__name__.lower()
    cls.chs_type = CTYPES[cls.ctype]
    cls.fields = [row.strip().split(None, 1)[0]
                  for row in cls.columns.strip().split('\n')]
    contactMaker[cls.ctype] = cls

def rName(tinfo):
    if tinfo in ('friend', 'group'):
        return CTYPES[tinfo]+'列表'
    else:
        return str(tinfo)+'的成员列表'

def tName(tinfo):
    if tinfo in ('friend', 'group'):
        return tinfo
    else:
        return tinfo.ctype+'_member_'+tinfo.uin

def tMaker(tinfo):
    return contactMaker[tinfo]

class ContactDB(object):
    def __init__(self, dbname=':memory:'):
        self.conn = sqlite3.connect(dbname)
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
    
    def Update(self, tinfo, contacts):
        tname, tmaker = tName(tinfo), tMaker(tinfo)
        
        try:
            if self.exist(tname):
                self.cursor.execute("DELETE FROM '%s'" % tname)
            else:
                sql = ("CREATE TABLE '%s' (" % tname) + tmaker.columns + ')'
                self.cursor.execute(sql)
            
            if contacts:
                w = ','.join(['?']*len(tmaker.fields))
                sql = "INSERT INTO '%s' VALUES(%s)" % (tname, w)
                self.cursor.executemany(sql, contacts)
        except:
            self.conn.rollback()
            traceback.print_exc()
            return None
        else:
            self.conn.commit()
            return rName(tinfo)