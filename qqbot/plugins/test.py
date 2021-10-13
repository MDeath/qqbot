# -*- coding: utf-8 -*-

import json

from admin import admin_ID
import __soup as soup

def onQQMessage(bot, Type, Sender, Source, Message): # 获取消息后调用此插件的函数执行
    '''\
    回复消息 解析 返回消息 类型和结构'''
    if Type not in ['Friend', 'Group']: # 消息来源 
        return
    Quote = {}
    At = []
    AtAll = False
    Plain = ''
    Image = []
    Xml = []
    Json = []
    for msg in Message:
        if msg.type == 'Quote':Quote = msg
        if msg.type == 'At':At.append(msg.target)
        if msg.type == 'AtAll':AtAll = True
        if msg.type == 'Face':pass
        if msg.type == 'Plain':Plain += msg.text
        if msg.type == 'Image':Image.append(msg)
        if msg.type == 'FlashImage':FlashImage = msg
        if msg.type == 'Voice':Voice = msg
        if msg.type == 'Xml':Xml.append(msg.xml)
        if msg.type == 'Json':Json.append(msg.json)
        if msg.type == 'App':App = msg.content
        if msg.type == 'Poke':pass 
        if msg.type == 'Dice':pass
        if msg.type == 'MusicShare':MusicShare = msg
        if msg.type == 'ForwardMessage':pass 
        if msg.type == 'File':pass
    if hasattr(Sender, 'group'):
        target = Sender.group.id
        if not admin_ID(bot, Sender.id,1):
            return
    else:
        target = Sender.id
    if Plain == '解析'and Quote:
        quote = Quote.id
        Quote = bot.MessageFromId(Quote.id)
        message = json.dumps(Quote.messageChain, ensure_ascii=False, indent=4)
        message = message.replace('\\\\', '\\')
        message = message.replace('\\\'','\'')
        message = message.replace('\\\"','\"')
        bot.SendMessage(Type, target, soup.Plain(message), quote=quote)