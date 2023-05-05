# -*- coding: utf-8 -*-

import soup
from admin import admin_ID
from common import JsonDict

def msgClear(Message):
    if isinstance(Message, list):
        for msg in Message:
            msgClear(msg)
    elif isinstance(Message, dict) or isinstance(Message, JsonDict):
        nk = []
        for k,v in Message.items():
            if v is None:
                nk.append(k)
        for k in nk:
            del Message[k]
    return Message

def onPlug(bot):
    bot.relay = set()
    bot.pack = {}

def onUnplug(bot):
    del bot.relay
    del bot.pack

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    开始广播 开启群广播 管理员权限以上
    广播结束 关闭群关播
    转发启用者消息至所有群'''
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = Sender.id, Sender.group.id

    Plain = ''
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text

    if Plain in ('广播结束','结束广播') and Sender.id in admin_ID(True,True) and Sender.id in bot.relay:
        bot.relay.remove(Sender.id)
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Sender.id in bot.relay:
        for g in bot.Group:
            if g.id != target:
                bot.SendMessage('group',g.id,*msgClear(Message))

    if Plain in ('广播开始','开始广播') and Sender.id in admin_ID(True,True) and Sender.id not in bot.relay:
        bot.relay.add(Sender.id)
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Plain in ('打包取消','取消打包') and Sender.id in admin_ID(True,True) and Sender.id in bot.pack:
        bot.pack.pop(Sender.id)
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Plain in ('打包结束','结束打包') and Sender.id in admin_ID(True,True) and Sender.id in bot.pack:
        Forward = soup.Forward(*[soup.Node(2854196310, 'QQ管家', *message) for message in bot.pack[Sender.id]])
        for g in bot.Group:
            if g.id != target:
                bot.SendMessage('group',g.id,Forward)
        bot.pack.pop(Sender.id)
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Sender.id in bot.pack:
        bot.pack[Sender.id].append(msgClear(Message))

    if Plain in ('打包开始','开始打包') and Sender.id in admin_ID(True,True) and Sender.id not in bot.pack:
        bot.pack[Sender.id] = []
        bot.SendMessage(Type,target,soup.Plain(Plain))