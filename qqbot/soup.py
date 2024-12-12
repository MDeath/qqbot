# -*- coding: utf-8 -*-

from time import time
import os
from common import JsonDict, b64dec, b64enc, jsonloads, jsondumps

class ParamError(BaseException):pass

class Base64(str):
    def __repr__(self) -> str:
        return f'[Base64] size:{len(self[9:])}'

def Type_Func(message:list|tuple, Type:list=None, Func=None):
    for msg in message:
        if msg['type'] in Type or Type is None:
            msg.update(Func(msg))
        elif msg['type'] == 'node' and 'content' in msg:
            Type_Func(msg.content)

def Source(
        id,
        t=None
    ):
    params = JsonDict(type="Source")
    params.id = id
    params.time = t or int(time())
    return params

def Reply(id:int):
    return JsonDict({"type": "reply", "id": id})

def Text(text:str):
    return JsonDict({"type": "text", "text": str(text)})

def At(uid:int=0):
    return JsonDict({"type": "at", "qq": uid})

def Face(id:int, big:bool=None):
    return JsonDict({"type": "face", "id": id,"big": big})

def FaceCount(id:int, count:bool=None):
    return JsonDict({"type": "bubble_face", "id": id,"count": count})

def media(file:str|bytes):
    '''file 可以是http、https、localpath、file、base64或是二进制'''
    if isinstance(file, str) and os.path.exists(file):
        with open(file,'rb') as f:file = f.read()
    if not (isinstance(file, str) and file.startswith(('http://','https://','file://'))):
        try:file = Base64('base64://'+b64enc(b64dec(file)))
        except:file = Base64('base64://'+b64enc(file))
    return file

def Image(file:str|bytes, type:str=None, subType:str=None):
    obj = JsonDict({"type": "image", "file":media(file)})
    if type:obj.type = type
    if subType:obj.data_type = subType
    return obj

def Voice(file:str|bytes):
    return JsonDict({"type": "record", "file":media(file)})

def Video(file:str|bytes):
    return JsonDict({"type": "video", "file":media(file)})

def Basketball(id:int):
    '5 没中, 4 擦边没中, 3 卡框, 2 擦边中, 1 正中'
    return JsonDict({{"type": "basketball", "id": id}})

def RPS(id:int):
    '锤 3 剪 2 布 1'
    return JsonDict({"type": "new_rps", "id": id})

def Dice(id:int):
    return JsonDict({"type": "new_dice", "id": id})

def Poke(uid:int,type:int=1,level:int=1):
    return JsonDict({"type": "poke", "type":type,"id": uid,"strength":level})

def Touch(uid:int):
    return JsonDict({"type": "touch", "id": uid})

def Music(url:str=None,audio:str=None,title:str=None,singer:str=None,image:str=None,type:str=None, id:int=None):
    '''\
type	string	✓	✓	是	音乐类型(qq/163)
id		int		✓	✓	是	音乐 ID
url		string	✓	✓	是	跳转链接
audio	string	✓	✓	是	音乐音频链接
title	string	✓	✓	是	标题
singer	string	✓	✓	是	歌手
image	string	✓	✓	否	封面图片链接'''
    obj = JsonDict({"type": "music", "type":type})
    if type in ('qq','163'):
        obj.data_type = type
        obj.data.id = id
    else:
        obj.data_type = 'custom'
        obj.url = url
        obj.audio = audio
        obj.title = title
        obj.singer = singer
        if image:obj.image = image
    return obj

def Weather(city:str=None,code:str=None):
    obj = JsonDict({"type": "weather",})
    if city:obj.city = city
    if code:obj.code = code
    return obj

def Location(lat:float, lon:float, title:str=None, content:str=None):
    obj = JsonDict({"type": "location", "lat":lat,"lon":lon})
    if title:obj.title = title
    if content:obj.content = content
    return obj

def Url(url:str,title:str=None,content:str=None,file:str=None):
    obj = JsonDict({"type": "share", "url":url})
    if title:obj.title = title
    if content:obj.content = content
    if file:obj.file = media(file)

def Gift(uid:int,id:id):
    return JsonDict({"type": "gift", "qq": uid,'id':id})

def Node(*message,id=None):
    obj = JsonDict({"type": "node"})
    if id:obj.id = id
    else:obj.content = message
    return obj

def Forward(id):
    return JsonDict(type='forward', id=id)

def Json(obj:object):
    try:jsonloads(obj)
    except:obj = jsondumps(obj)
    return JsonDict({"type": "json", "data": obj})