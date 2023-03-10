# -*- coding: utf-8 -*-

import soup
from admin import admin_ID
from common import JsonDict

def msgClear(Message):
    if type(Message) is list:
        for msg in Message:
            msgClear(msg)
    elif type(Message) is dict or isinstance(Message,dict):
        nk = []
        for k,v in Message.items():
            if v is None:
                nk.append(k)
        for k in nk:
            del Message[k]
    return Message

def onPlug(bot):bot.relay=set()

def onUnplug(bot):del bot.relay

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

    if Plain.startswith('广播结束') and Sender.id in admin_ID(True,True) and Sender.id in bot.relay:
        bot.relay.remove(Sender.id)
        bot.SendMessage(Type,target,soup.Plain('结束'))

    if Sender.id in bot.relay:
        for g in bot.Group:
            if g.id != target:
                bot.SendMessage('group',g.id,*msgClear(Message))

    if Plain.startswith('开始广播') and Sender.id in admin_ID(True,True) and Sender.id not in bot.relay:
        bot.relay.add(Sender.id)
        bot.SendMessage(Type,target,soup.Plain('开始'))