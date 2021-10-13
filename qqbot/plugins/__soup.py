# -*- coding: utf-8 -*-

from time import time

def Source(id,t=None):
    return {
        "type": "Source",
        "id": 123456,
        "time": t or int(time())
    }

def Quote(sender,target,id=None,*message:dict):
    return {
        "type": "Quote",
        "id": id,
        "groupId": 0,
        "senderId": sender,
        "targetId": target,
        "origin": [msg for msg in message]
    }

def At(id:int) -> list:
    # target | Long | 群员QQ号
    return {"type": "At","target": id}

def AtAll() -> dict:
    return {"type": "AtAll"}

def Face(id:int=None, name:str=None):
    # id   | Int     | QQ表情编号，可选，优先高于name
    # name | String  | QQ表情拼音，可选
    return {
        "type": "Face",
        "faceId": id,
        "name": name
    }

def Plain(s:str) -> dict:
    # text | String | 文字消息
    return {"type": "Plain","text": s}

def Image(url=None, path=None, base64=None, id=None) -> dict:
    # id     | String | 图片的id，群图片与好友图片格式不同。不为空时将忽略url属性
    # url    | String | 图片的URL，发送时可作网络图片的链接；接收时为腾讯图片服务器的链接，可用于图片下载
    # path   | String | 图片的路径，发送本地图片，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径
    # base64 | String | 图片的 Base64 编码
    return {
        "type": "Image",
        "imageId": id,
        "url": url,
        "path": path,
        "base64": base64
    }

def FlashImage(url=None, path=None, base64=None, id=None) -> dict:
    # 同 `Image`
    return {
        "type": "Image",
        "imageId": id,
        "url": url,
        "path": path,
        "base64": base64
    }

def Voice(url=None, path=None, base64=None, id=None) -> dict:
    # id     | String | 语音的id，不为空时将忽略url属性
    # url    | String | 语音的URL，发送时可作网络语音的链接；接收时为腾讯语音服务器的链接，可用于语音下载
    # path   | String | 语音的路径，发送本地语音，路径相对于 JVM 工作路径（默认是当前路径，可通过 `-Duser.dir=...`指定），也可传入绝对路径。
    # base64 | String | 语音的 Base64 编码
    # length | Long   | 返回的语音长度, 发送消息时可以不传

    #> 参数任选其一，出现多个参数时，按照id > url > path > base64的优先级
    return {
        "type": "Image",
        "imageId": id,
        "url": url,
        "path": path,
        "base64": base64
    }

def Xml(xml:str) -> dict:
    # xml | String | XML文本
    return {"type": "Xml","xml": xml}

def Json(json:str):
    # json | String | Json文本
    return {"type": "Json","json": json}

def App(content:str):
    # content | String | 内容    |
    return {"type": "App","content": content}
    
def Poke(name:str):
    # name | String | 戳一戳的类型
    # 1. "Poke": 戳一戳
    # 2. "ShowLove": 比心
    # 3. "Like": 点赞
    # 4. "Heartbroken": 心碎
    # 5. "SixSixSix": 666
    # 6. "FangDaZhao": 放大招
    return {"type": "Poke","name": name}

def Dice(value:int):
    # value | Int | 点数
    return {"type": "Dice","value": value}
    
def MusicShare(kind=None,title=None,summary=None,jumpUrl=None,pictureUrl=None,musicUrl=None,brief=None):
    # kind       | String | 类型
    # title      | String | 标题
    # summary    | String | 概括
    # jumpUrl    | String | 跳转路径
    # pictureUrl | String | 封面路径
    # musicUrl   | String | 音源路径
    # brief      | String | 简介
    return {
        "type": "MusicShare",
        "kind": kind,
        "title": title,
        "summary": summary,
        "jumpUrl": jumpUrl,
        "pictureUrl": pictureUrl,
        "musicUrl": musicUrl,
        "brief": brief
    }
    
def Forward(*node:dict) -> dict:
    # nodeList | object | 消息节点
    return {
        "type": "Forward",
        "nodeList": [n for n in node]
    }

def Node(sender:int=None,name:str=None,*message:dict,t:int=None,id:int=None) -> dict:
    # senderid   | Long   | 发送人QQ号
    # time       | Int    | 发送时间
    # senderName | String | 显示名称
    # message    | Array  | 消息数组
    # id         | Int    | 可以只使用消息id，从缓存中读取一条消息作为节点
    return {
        "senderId": sender or None,
        "time": t or (int(time())if not id else None),
        "senderName": name or None,
        "messageChain": [msg for msg in message],
        "messageId": id
    }

def File(id=None,name=None,size=None):
    # id   | String | 文件识别id
    # name | String | 文件名
    # size | Long   | 文件大小
    return {
        "type": "File",
        "id": id,
        "name": name,
        "size": size
    }

def MiraiCode(MiraiCode):
    # code | String | MiraiCode
    # MiraiCode的使用(https://github.com/mamoe/mirai/blob/dev/docs/Messages.md#%E6%B6%88%E6%81%AF%E5%85%83%E7%B4%A0)
    return{"type": "MiraiCode","code": MiraiCode}
