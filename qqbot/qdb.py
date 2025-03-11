import traceback, sqlite3

from mainloop import Put, PutBack
from common import DotDict, JsonDict, jsondumps

def DataDump(dataLS:list|dict|tuple): # 把非 str, int 类型转为 json 或文本
    '把数据库不支持的 数据 或 数据列表 转换成 json 或 str'
    if isinstance(dataLS,(list,tuple)) and all([isinstance(data,(list,tuple,dict)) for data in dataLS]):
        for data in dataLS:return DataDump(data)
    if isinstance(dataLS, (list,tuple)):items = [[k,dataLS[k]] for k in range(len(dataLS))]
    elif isinstance(dataLS, dict):items = dataLS.items()
    else:raise TypeError('数据必须是 dict 或 list')
    for k, v in items:
        if isinstance(v, (bool, float, int, type(None), str)):continue
        try:dataLS[k] = jsondumps(v, ensure_ascii=False)
        except:dataLS[k] = str(v)

class DataObj(JsonDict):
    '继承后设置 columns 第一条必须是 PRIMARY KEY    NOT NULL'
    columns = '''\
id          INTEGER     PRIMARY KEY     NOT NULL,
time        REAL,
'''

    def __init__(self, *fields):
        self.fields = [row.strip().split(None, 1)[0] for row in self.columns.strip().splitlines()]
        for k, field in zip(self.fields, fields):
            try:self.__dict__[k] = DotDict(field)
            except:self.__dict__[k] = field

    def __repr__(self):
        return f'{self.__class__.__name__.lower()}-{self.fields[0]}="{getattr(self,self.fields[0])}"'

def Create_DataObj(tname, columns):return type(tname, (DataObj,), {'columns': columns})

def _work(func):
    def _temp(*args, **kwargs):
        try:return func(*args, **kwargs)
        except sqlite3.ProgrammingError:return PutBack(func, *args, **kwargs)
    return _temp

class DataBase(object):
    def __init__(self, dbname=':memory:'):
        self.conn = sqlite3.connect(dbname)
        self.conn.text_factory = str
        self.cursor = self.conn.cursor()
        # 读取表和sql，创建表数据对象
        self.cursor.execute('SELECT name, sql FROM "main".sqlite_master')
        self.Add_Tabel_DataObj(*self.cursor.fetchall())
        for func in [self.update, self.insert, self.modify, self.exist, self.count, self.selectAll, self.select, self.delete]:
            setattr(self, func.__name__.title(), _work(func))

    Table = {}
    def Add_Tabel_DataObj(self, *Class:list|tuple|DataObj):
        '注册表数据对象，可以是继承 DataObj 的对象列表，或是自定义 name 和 columns 的列表'
        for cls in Class:
            if isinstance(cls, (list,tuple)) and len(cls) == 2:
                name = cls[0]
                if cls[1].startswith("CREATE TABLE 'msglog' ("):columns = cls[1].split('\n)')[0].split("(")[1]
                else:columns = cls[1]
                cls = Create_DataObj(name, columns)
            cls.fields = [row.strip().split(None, 1)[0] for row in cls.columns.strip().splitlines()]
            self.Table[cls.__name__] = cls

    def update(self, tname:str, *dataLS:list|dict) -> str:
        '新增或更新所有'
        tmaker = self.Table[tname]
        DataDump(dataLS)
        try:
            if self.exist(tname):
                for data in dataLS:
                    cl = self.select(tname, tmaker.fields[0], data[0])
                    if cl:
                        self.modify(tname, tmaker.fields[0], data[0], **dict(zip(tmaker.fields[1:],data[1:])))
                    else:
                        self.insert(tname, dataLS)

            else:
                self.insert(tname, dataLS)
        except:
            self.conn.rollback()
            traceback.print_exc()
            return None
        else:
            self.conn.commit()
            return tname

    def insert(self, tname:str, *dataLS:list|dict) -> str:
        '新增'
        tmaker = self.Table[tname]
        DataDump(dataLS)
        
        try:
            if not self.exist(tname):
                self.cursor.execute(f"CREATE TABLE '{tname}' ({tmaker.columns})")
            if dataLS and all([isinstance(data,list) for data in dataLS]):
                w = ','.join(['?']*len(tmaker.fields))
                sql = f"INSERT INTO '{tname}' VALUES ({w})"
                self.cursor.executemany(sql, dataLS)
            elif dataLS and all([isinstance(data,dict) for data in dataLS]):
                for data in dataLS:
                    self.cursor.execute(f"INSERT INTO '{tname}' ({','.join(data.keys())}) VALUES ({','.join(['?']*len(data))})", list(data.values()))
        except:
            self.conn.rollback()
            traceback.print_exc()
            return None
        else:
            self.conn.commit()
            return tname
    
    def modify(self, tname:str, where:str, value:str=None, like:bool=False, **kw) -> list[DataObj]:
        '修改'
        tmaker = self.Table[tname]
        DataDump(kw)

        for column in kw.keys():
            assert column in tmaker.fields

        try:
            if not value:
                self.cursor.execute(f"UPDATE '{tname}' SET {','.join([f'{k}={v}' for k, v in kw.items()])} WHERE {where}")
            elif not like:
                self.cursor.execute(f"UPDATE '{tname}' SET {','.join([f'{k}={v}' for k, v in kw.items()])} WHERE {where}={value}")
            else:
                self.cursor.execute(f"UPDATE '{tname}' SET {','.join([f'{k}={v}' for k, v in kw.items()])} WHERE {where} like %{value}%")
        except:
            self.conn.rollback()
            traceback.print_exc()
            return False
        else:
            self.conn.commit()
            return self.select(tname, where)
    
    def exist(self, tname:str) -> bool:
        '检查表存在'
        self.cursor.execute(
            ("SELECT tbl_name FROM sqlite_master "
             f"WHERE type='table' AND tbl_name='{tname}'")
        )
        return bool(self.cursor.fetchall())

    def count(self, tname:str, where:str=None, value:str=None, like:bool=False) -> int:
        if not self.exist(tname):return []
        if not where:
            self.cursor.execute(f"SELECT COUNT(*) FROM '{tname}'")
        elif not value:
            self.cursor.execute(f"SELECT COUNT(*) FROM '{tname}' WHERE {where}")
        elif not like:
            self.cursor.execute(f"SELECT COUNT(*) FROM '{tname}' WHERE {where}={value}")
        else:
            self.cursor.execute(f"SELECT COUNT(*) FROM '{tname}' WHERE {where} like %{value}%")
        return self.cursor.fetchall()[0][0]

    def selectAll(self, tname:str, limit=()) -> list[DataObj]:
        '整表查询'
        if not self.exist(tname):return []
        limit = f' LIMIT {",".join([str(n) for n in limit])}' if limit else ''
        self.cursor.execute(f"SELECT * FROM '{tname}'{limit}")
        return [self.Table[tname](*item) for item in self.cursor.fetchall()]
    
    def select(self, tname:str, where:str=None, value:str=None, like:bool=False, limit=()) -> list[DataObj]:
        '高级查询'
        if not self.exist(tname):return []
        limit = f' LIMIT {",".join([str(n) for n in limit])}' if limit else ''
        if not where:
            self.cursor.execute(f"SELECT * FROM '{tname}'{limit}")
        elif not value:
            self.cursor.execute(f"SELECT * FROM '{tname}' WHERE {where}{limit}")
        elif not like:
            self.cursor.execute(f"SELECT * FROM '{tname}' WHERE {where}={value}{limit}")
        else:
            self.cursor.execute(f"SELECT * FROM '{tname}' WHERE {where} like %{value}%{limit}")
        return [self.Table[tname](*item) for item in self.cursor.fetchall()]

    def delete(self, tname:str, where:str) -> bool:
        '删除'
        try:
            self.cursor.execute(f"DELETE FROM '{tname}' WHERE {where}")
        except:
            self.conn.rollback()
            traceback.print_exc()
            return False
        else:
            self.conn.commit()
            return True
# 以上只能主线程调用；以下为多线程和主线程均可调用，使用 PutBack 套 Put 实现，可做用于插件和命令行中
    def Execute(self, sql, parameters=()):
        try:
            self.cursor.execute(sql, parameters)
            self.conn.commit()
            return self.cursor.fetchall()
        except sqlite3.ProgrammingError:
            Put(self.cursor.execute, sql, parameters)
            Put(self.conn.commit)
            return PutBack(self.cursor.fetchall)
        except:
            try:self.conn.rollback()
            except sqlite3.ProgrammingError:Put(self.conn.rollback)

    def Executemany(self, sql, parameters=()):
        try:
            self.cursor.executemany(sql, parameters)
            return self.cursor.fetchall()
        except sqlite3.ProgrammingError:
            Put(self.cursor.executemany, sql, parameters)
            return PutBack(self.cursor.fetchall)
