# -*- coding: utf-8 -*-

import sqlite3, traceback

TAGS = ('id=', 'name=', 'mark=', 'title=')

CTYPES = {
    'friend': '好友', 'group': '群', 'group-member': '成员'
}

class QContact(object):
    def __init__(self, *fields):
        for k, field in zip(self.fields, fields):
            self.__dict__[k] = field
        self.__dict__['ctype'] = self.__class__.ctype

    def __repr__(self):
        return f'{self.chs_type}“{self.name}”'

    def __setattr__(self, k, v):
        raise TypeError("QContact object is readonly")

class Friend(QContact):
    columns = '''\
        id INTEGER PRIMARY KEY,
        name VARCHAR(80),
        mark VARCHAR(80)
    '''

class Group(QContact):
    columns = '''\
        id INTEGER PRIMARY KEY,
        name VARCHAR(80),
        permission VARCHAR(13)
    '''

class GroupMember(QContact):
    columns = '''\
        id INTEGER PRIMARY KEY,
        name VARCHAR(80),
        title VARCHAR(80),
        permission VARCHAR(13),
        joinTimestamp INTEGER,
        lastSpeakTimestamp INTEGER,
        muteTimeRemaining INTEGER
    '''

contactMaker = {}

for cls in [Friend, Group, GroupMember]:
    cls.ctype = cls.__name__.lower().replace('member', '-member')
    cls.chs_type = CTYPES[cls.ctype]
    cls.fields = [row.strip().split(None, 1)[0]
                  for row in cls.columns.strip().split('\n')]
    contactMaker[cls.ctype] = cls

def tName(tinfo):
    if tinfo in ('friend', 'group'):
        return tinfo
    else:
        assert type(tinfo.id) is int or tinfo.id.isdigit()
        return f'{tinfo.ctype}_member_{tinfo.id}'

def rName(tinfo):
    if tinfo in ('friend', 'group'):
        return CTYPES[tinfo]+'列表'
    else:
        return str(tinfo)+'的成员列表'

def tType(tinfo):
    if tinfo in ('friend', 'group'):
        return tinfo
    else:
        return tinfo.ctype + '-member'

def tMaker(tinfo):
    return contactMaker[tType(tinfo)]

class ContactDB(object):
    def __init__(self, dbname=':memory:'):
        self.conn = sqlite3.connect(dbname)
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
    
    def Update(self, tinfo, contacts):
        tname, tmaker = tName(tinfo), tMaker(tinfo)
        
        w = ','.join(['?']*len(tmaker.fields))
        sql = "INSERT INTO '%s' VALUES(%s)" % (tname, w)
        try:
            if self.exist(tname):
                for contact in contacts:
                    cl = self.select(tname, tmaker.fields[0], contact[0])
                    if cl:
                        self.Modify(tinfo, cl, **dict(zip(tmaker.fields[1:],contact[1:])))
                    else:
                        self.cursor.execute(sql, contact)
            
            else:
                self.cursor.execute(f"CREATE TABLE '{tname}' ({tmaker.columns})")
                if contacts:
                    self.cursor.executemany(sql, contacts)
        except:
            self.conn.rollback()
            traceback.print_exc()
            return None
        else:
            self.conn.commit()
            return rName(tinfo)
    
    def List(self, tinfo, cinfo=None):
        tname, tmaker = tName(tinfo), tMaker(tinfo)

        if not self.exist(tname):
            return None
            
        if cinfo is None:
            items = self.selectAll(tname)
        elif cinfo == '':
            items = []
        else:
            like = False
            if type(cinfo) is int or cinfo.isdigit():
                column = 'id'
            else:
                for tag in TAGS:
                    if cinfo.startswith(tag):
                        column = tag[:-1]
                        cinfo = cinfo[len(tag):]
                        break
                    if cinfo.startswith(tag[:-1]+':like:'):
                        column = tag[:-1]
                        cinfo = cinfo[(len(tag)+5):]
                        if not cinfo:
                            return []
                        like = True
                        break
                else:
                    if cinfo.startswith(':like:'):
                        cinfo = cinfo[6:]
                        if not cinfo:
                            return []
                        if cinfo.isdigit():
                            column = 'id'
                        else:
                            column = 'name'
                        like = True
                    else:
                        column = 'name'
                
            if column not in tmaker.fields:
                return []

            items = self.select(tname, column, cinfo, like)
        
        return [tmaker(*item) for item in items]
    
    def exist(self, tname):
        self.cursor.execute(
            ("SELECT tbl_name FROM sqlite_master "
             "WHERE type='table' AND tbl_name='%s'") % tname
        )
        return bool(self.cursor.fetchall())

    def select(self, tname, column, value, like=False):
        if not like:
            sql = "SELECT * FROM '%s' WHERE %s=?" % (tname, column)
        else:
            value = '%' + value + '%'
            sql = "SELECT * FROM '%s' WHERE %s like ?" % (tname, column)
        self.cursor.execute(sql, (value,))
        return self.cursor.fetchall()

    def selectAll(self, tname):
        self.cursor.execute("SELECT * FROM '%s'" % tname)
        return self.cursor.fetchall()
    
    def Delete(self, tinfo, c):
        tname = tName(tinfo)
        try:
            self.cursor.execute("DELETE FROM '%s' WHERE id=?" % tname, [c.id])
        except:
            self.conn.rollback()
            traceback.print_exc()
            return False
        else:
            self.conn.commit()
            return True
    
    def Modify(self, tinfo, c, **kw):
        tname, tmaker = tName(tinfo), tMaker(tinfo)
        colstr, values = [], []

        for column, value in kw.items():
            assert column in tmaker.fields
            colstr.append("%s=?" % column)
            values.append(value)
            c.__dict__[column] = value

        values.append(c.id)

        sql = "UPDATE '%s' SET %s WHERE id=?" % (tname, ','.join(colstr))
        try:
            self.cursor.execute(sql, values)
        except:
            self.conn.rollback()
            traceback.print_exc()
            return False
        else:
            self.conn.commit()
            return True

    @classmethod
    def NullContact(cls, tinfo, id):
        tmaker = tMaker(tinfo)
        fields = []
        for row in tmaker.columns.strip().split('\n'):
            field, ftype = row.strip().split(None, 1)
            if field == 'id':
                val = id
            elif field == 'name':
                val = 'id' + id
            elif ftype.startswith('VARCHAR'):
                val = '#NULL'
            else:
                val = -1
            fields.append(val)
        return tmaker(*fields)

if __name__ == '__main__':
    db = ContactDB()
    db.Update('friend', [
        ['1234567890', 'nick昵称1', 'mark备注1'],
        [9876543210, 'nick昵称2', 'mark备注2']
    ])
    bl = db.List('friend')
    print(bl, bl[0].__dict__)

    print(db.List('friend', 'name:like:nick昵称2'))
    print(db.List('friend', 'nick昵称1'))

    db.Update('group', [
        ['1234567890', '群1', 'OWNER'],
        [9876543210, '群2', 'ADMINISTRATOR']
    ])
    
    print(db.List('group', 1234567890))
    g = db.List('group', 'id:like:123456')[0]
    
    db.Update(g, [
        ['1234567890', '昵称1', '头衔1', 'OWNER', 123456, 78944, 0],
        [9876543210, '昵称2', '头衔2', 'ADMINISTRATOR', 123456, 78944, 0]  
    ])
    
    print(db.List(g, 'name:like:昵称'))
    print(db.List(g, '1234567890'))
    print(db.List(g, '昵称2'))
    print(db.List(g, ':like:昵称'))
    print(db.List(g, ':like:1'))