# -*- coding: utf-8 -*-

from time import time
from common import JsonDict

def Source(id,t=None):
    params = {"type": "Source"}
    params["id"] = id
    params["time"] = t or int(time())
    return JsonDict(params)

def Quote(sender,target,*message:dict,id=None):
    '''\
sender  | Long   | 被引用回复的原消息的发送者的QQ号
target  | Long   | 被引用回复的原消息的接收者者的QQ号（或群号）
id      | Int    | 被引用回复的原消息的messageId
message | Object | 被引用回复的原消息的消息链对象'''
    params = {"type": "Quote"}
    if sender:params["senderId"] = sender
    if target:params["targetId"] = target
    if id:params["id"] = id
    if message:params["origin"] = [msg for msg in message]
    return JsonDict(params)

def At(id:int) -> list:
    '''\
target | Long | 群员QQ号'''
    return JsonDict({"type": "At","target": id})

def AtAll() -> dict:
    return JsonDict({"type": "AtAll"})

def Face(id:int=None, name:str=None):
    '''\
id   | Int     | QQ表情编号，可选，优先高于name
name | String  | QQ表情拼音，可选'''
    params = {"type": "Face"}
    if id:params["faceId":] = id
    if name:params["name"] = name
    return JsonDict(params)

def Plain(s:str) -> dict:
    '''\
text | String | 文字消息'''
    return JsonDict({"type": "Plain","text": str(s)})

def Image(url=None, path=None, base64=None, id=None) -> dict:
    '''\
url    | String | 图片的URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载
path   | String | 图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径
base64 | String | 图片的 Base64 编码
id     | String | 图片的id，群图片与好友图片格式不同。不为空时将忽略url属性'''
    params = {"type": "Image"}
    if url:params["url"] = url
    if path:params["path"] = path
    if base64:params["base64"] = base64
    if id:params["imageId"] = id
    return JsonDict(params)

def FlashImage(url=None, path=None, base64=None, id=None) -> dict:
    '''\
url    | String | 图片的URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载
path   | String | 图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径
base64 | String | 图片的 Base64 编码
id     | String | 图片的id，群图片与好友图片格式不同。不为空时将忽略url属性'''
    params = {"type": "FlashImage"}
    if id:params["imageId"] = id
    if url:params["url"] = url
    if path:params["path"] = path
    if base64:params["base64"] = base64
    return JsonDict(params)

def Voice(url=None, path=None, base64=None, id=None) -> dict:
    '''\
url    | String | 语音的URL，发送时可作网络语音的链接；接收时为腾讯语音服务器的链接，可用于语音下载
path   | String | 语音的路径，发送本地语音，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径。
base64 | String | 语音的 Base64 编码
id     | String | 语音的id，不为空时将忽略url属性

#> 参数任选其一，出现多个参数时，按照id > url > path > base64的优先级'''
    params = {"type": "Voice"}
    if id:params["voiceId"] = id
    if url:params["url"] = url
    if path:params["path"] = path
    if base64:params["base64"] = base64
    return JsonDict(params)

def Xml(xml:str) -> dict:
    '''\
xml | String | XML文本'''
    return JsonDict({"type": "Xml","xml": xml})

def Json(json:str):
    '''\
json | String | Json文本'''
    return JsonDict({"type": "Json","json": json})

def App(content:str):
    '''\
content | String | 内容'''
    return JsonDict({"type": "App","content": content})
    
def Poke(name:str):
    '''\
name | String | 戳一戳的类型
1. "Poke": 戳一戳
2. "ShowLove": 比心
3. "Like": 点赞
4. "Heartbroken": 心碎
5. "SixSixSix": 666
6. "FangDaZhao": 放大招'''
    return JsonDict({"type": "Poke","name": name})

def Dice(value:int):
    '''\
value | Int | 点数'''
    return JsonDict({"type": "Dice","value": value})
    
def MusicShare(kind=None,title=None,summary=None,jumpUrl=None,pictureUrl=None,musicUrl=None,brief=None):
    '''\
kind       | String | 类型
title      | String | 标题
summary    | String | 概括
jumpUrl    | String | 跳转路径
pictureUrl | String | 封面路径
musicUrl   | String | 音源路径
brief      | String | 简介'''
    params = {"type": "MusicShare"}
    if kind:params["kind"] = kind
    if title:params["title"] = title
    if summary:params["summary"] = summary
    if jumpUrl:params["jumpUrl"] = jumpUrl
    if pictureUrl:params["pictureUrl"] = pictureUrl
    if musicUrl:params["musicUrl"] = musicUrl
    if brief:params["brief"] = brief
    return JsonDict(params)
    
def Forward(*node:dict) -> dict:
    '''\
nodeList | object | 消息节点'''
    return JsonDict({
        "type": "Forward",
        "nodeList": [n for n in node]
    })

def Node(sender:int=None,name:str=None,*message:dict,t:int=None,id:int=None) -> dict:
    '''\
senderid   | Long   | 发送人QQ号
time       | Int    | 发送时间
senderName | String | 显示名称
message    | Array  | 消息数组
id         | Int    | 可以只使用消息id，从缓存中读取一条消息作为节点'''
    params = {}
    if sender:params['senderId'] = sender
    if name:params['senderName'] = name
    params['messageChain'] = [msg for msg in message]
    if t:params['time'] = t or (int(time())if not id else None)
    if id:params['messageId'] = id
    return JsonDict(params)

def File(id=None,name=None,size=None):
    '''\
id   | String | 文件识别id
name | String | 文件名
size | Long   | 文件大小'''
    return JsonDict({
        "type": "File",
        "id": id,
        "name": name,
        "size": size
    })

def MiraiCode(MiraiCode):
    '''\
code | String | MiraiCode
MiraiCode的使用(https://github.com/mamoe/mirai/blob/dev/docs/Messages.md#%E6%B6%88%E6%81%AF%E5%85%83%E7%B4%A0)'''
    return JsonDict({"type": "MiraiCode","code": MiraiCode})
