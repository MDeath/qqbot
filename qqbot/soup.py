# -*- coding: utf-8 -*-

from time import time
from common import DotDict

class ParamError(BaseException):pass

def Source(
        id,
        t=None
    ):
    params = {"type": "Source"}
    params["id"] = id
    params["time"] = t or int(time())
    return DotDict(params)

def Quote(
        sender:int,
        target:int,
        *message:dict,
        id:int=None
    ):
    '''\
sender  | Int    | 被引用回复的原消息的发送者的QQ号
target  | Int    | 被引用回复的原消息的接收者者的QQ号（或群号）
id      | Int    | 被引用回复的原消息的messageId
message | Object | 被引用回复的原消息的消息链对象'''
    params = {"type": "Quote"}
    if sender:params["senderId"] = sender
    if target:params["targetId"] = target
    if id:params["id"] = id
    if message:params["origin"] = list(message)
    return DotDict(params)

def At(
        id:int
    ) -> list:
    '''\
target | Int | 群员QQ号'''
    return DotDict({"type": "At","target": id})

def AtAll() -> dict:
    return DotDict({"type": "AtAll"})

def Face(
        id:int=None, 
        name:str=None
    ):
    '''\
id   | Int | QQ表情编号，可选，优先高于name
name | Str | QQ表情拼音，可选'''
    params = {"type": "Face"}
    if id:params["faceId"] = id
    if name:params["name"] = name
    return DotDict(params)

def Plain(s:str) -> dict:
    '''\
text | Str | 文字消息'''
    return DotDict({"type": "Plain","text": str(s)})

def Image(
        url:str=None, 
        path:str=None, 
        base64:str|bytes|dict=None, 
        id=None
    ) -> dict:
    '''\
url    | Str | 图片的URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载
path   | Str | 图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径
base64 | Str | 图片的 Base64 编码，或者图片的URL
id     | Str | 图片的id，群图片与好友图片格式不同。不为空时将忽略url属性'''
    params = {"type": "Image"}
    if url:params["url"] = url
    if path:params["path"] = path
    if id:params["imageId"] = id
    if base64:params["base64"] = base64
    return DotDict(params)

def FlashImage(
        url:str=None, 
        path:str=None, 
        base64:str|bytes|dict=None, 
        id=None
    ) -> dict:
    '''\
url    | Str | 图片的URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载
path   | Str | 图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径
base64 | Str | 图片的 Base64 编码，或者图片的URL
id     | Str | 图片的id，群图片与好友图片格式不同。不为空时将忽略url属性'''
    params = {"type": "FlashImage"}
    if url:params["url"] = url
    if path:params["path"] = path
    if id:params["imageId"] = id
    if base64:params["base64"] = base64
    return DotDict(params)

def Voice(
        url:str=None, 
        path:str=None, 
        base64:str|bytes|dict=None, 
        id=None
    ) -> dict:
    '''\
url    | Str | 语音的URL，发送时可作网络语音的链接；接收时为腾讯语音服务器的链接，可用于语音下载
path   | Str | 语音的路径，发送本地语音，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径。
base64 | Str | 语音的 Base64 编码，或者语音的URL
id     | Str | 语音的id，不为空时将忽略url属性

#> 参数任选其一，出现多个参数时，按照id > url > path > base64的优先级'''
    params = {"type": "Voice"}
    if url:params["url"] = url
    if path:params["path"] = path
    if id:params["voiceId"] = id
    if base64:params["base64"] = base64
    return DotDict(params)

def Xml(xml:str) -> dict:
    '''\
xml | Str | XML文本'''
    return DotDict({"type": "Xml","xml": xml})

def Json(json:str):
    '''\
json | Str | Json文本'''
    return DotDict({"type": "Json","json": json})

def App(content:str):
    '''\
content | Str | 内容'''
    return DotDict({"type": "App","content": content})
    
def Poke(name:str):
    '''\
name | Str | 戳一戳的类型
1. "Poke": 戳一戳
2. "ShowLove": 比心
3. "Like": 点赞
4. "Heartbroken": 心碎
5. "SixSixSix": 666
6. "FangDaZhao": 放大招'''
    return DotDict({"type": "Poke","name": name})

def Dice(value:int):
    '''\
value | Int | 点数'''
    return DotDict({"type": "Dice","value": value})
    
def MusicShare(
        kind=None,
        title=None,
        summary=None,
        jumpUrl=None,
        pictureUrl=None,
        musicUrl=None,
        brief=None
    ):
    '''\
kind       | Str | 类型
title      | Str | 标题
summary    | Str | 概括
jumpUrl    | Str | 跳转路径
pictureUrl | Str | 封面路径
musicUrl   | Str | 音源路径
brief      | Str | 简介'''
    params = {"type": "MusicShare"}
    if kind:params["kind"] = kind
    if title:params["title"] = title
    if summary:params["summary"] = summary
    if jumpUrl:params["jumpUrl"] = jumpUrl
    if pictureUrl:params["pictureUrl"] = pictureUrl
    if musicUrl:params["musicUrl"] = musicUrl
    if brief:params["brief"] = brief
    return DotDict(params)
    
def Forward(
    *node:dict,
    title:str=None,
    brief:str=None,
    summary:str=None,
    preview:list=None,
    source:str=None
) -> dict:
    '''\
nodeList | object | 消息节点
title    | Str    | 标题（群聊的聊天记录）
brief    | Str    | 简介（[聊天记录]）
summary  | Str    | 总结（查看x条转发消息）
preview  | List   | 预览（["msg1", "msg2", "msg3", "msg4"]）
source   | Str    | 来源（聊天记录）'''
    params = {
        "type": "Forward",
        "nodeList": list(node)
    }
    if title or brief or source or preview or summary:
        params['display'] = {}
        if title:params['display']['title'] = title
        if brief:params['display']['brief'] = brief
        if source:params['display']['source'] = source
        if preview:params['display']['preview'] = preview
        if summary:params['display']['summary'] = summary
    return DotDict(params)

def Node(
    sender:int=None,
    name:str=None,
    *message:dict,
    t:int=None,
    target:int=None,
    id:int=None,
    ref:dict|list|tuple=None
) -> dict:
    '''\
senderid   | Int             | 发送人QQ号
time       | Int             | 发送时间
senderName | Str             | 显示名称
message    | List            | 消息数组
id         | Int             | 可以只使用消息id，从缓存中读取一条消息作为节点
target     | Int             | 引用的上下文目标，群号、好友账号
ref        | Dict|List|Tuple | {'id' or 'messageId':Int,'target':Int} 或者 [target:Int,messageId:Int]'''
    params = {}
    if sender:params['senderId'] = sender
    if not name:name = str(sender)
    if name:params['senderName'] = name
    params['messageChain'] = list(message)
    params['time'] = t or (int(time())if not id else None)

    if ref:
        if type(ref) in [list,tuple]:params['messageRef'] = {'target':ref[0],'messageId':ref[1]}
        else:
            if 'messageId' in ref and 'target' in ref:params['messageRef'] = ref
            elif 'id' in ref and 'target' in ref:params['messageRef'] = {'target':ref['target'],'messageId':ref['id']}
            else:raise ParamError('Error:The key of ref is only (id or messageId) and target')
    elif target:
        if not id:raise ParamError('Error:id is None')
        else:params['messageRef'] = {'messageId':id,'target':target}
    elif id:params['messageId'] = id
    return DotDict(params)

def File(
    id=None,
    name=None,
    size=None
):
    '''\
id   | Str | 文件识别id
name | Str | 文件名
size | Int   | 文件大小'''
    return DotDict({
        "type": "File",
        "id": id,
        "name": name,
        "size": size
    })

def MiraiCode(MiraiCode):
    '''\
code | Str | MiraiCode
MiraiCode的使用(https://github.com/mamoe/mirai/blob/dev/docs/Messages.md#%E6%B6%88%E6%81%AF%E5%85%83%E7%B4%A0)'''
    return DotDict({"type": "MiraiCode","code": MiraiCode})
