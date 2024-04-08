# -*- coding: utf-8 -*-

import soup
from admin import admin_ID
from common import JsonDict
from qr import fwimg2qr

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

relay = set()
pack = {}
def onPlug(bot):
    global relay
    global pack
    relay = set()
    pack = {}

def onUnplug(bot):
    global relay
    global pack
    del relay
    del pack

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    开始广播 开启群广播 管理员权限以上
    广播结束 关闭群关播
    转发启用者消息至所有群
    开始打包 开始收集消息 管理员权限以上
    打包结束 合并消息发送至所有群
    取消打包 放弃所有消息'''
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

    if Plain in ('广播结束','结束广播') and Sender.id in admin_ID(True,True) and f'{target}{Sender.id}' in relay:
        relay.remove(f'{target}{Sender.id}')
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if f'{target}{Sender.id}' in relay:
        for g in bot.Group:
            if g.id != target:
                bot.SendMessage('group',g.id,*msgClear(Message))

    if Plain in ('广播开始','开始广播') and Sender.id in admin_ID(True,True) and f'{target}{Sender.id}' not in relay:
        relay.add(f'{target}{Sender.id}')
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Plain in ('打包取消','取消打包') and Sender.id in admin_ID(True,True) and f'{target}{Sender.id}' in pack:
        pack.pop(f'{target}{Sender.id}')
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if Plain in ('打包结束','结束打包') and Sender.id in admin_ID(True,True) and f'{target}{Sender.id}' in pack:
        node = [soup.Node(2854196310, 'QQ管家', *message) for message in pack[f'{target}{Sender.id}']]
        for g in bot.Group:
            if g.id == target:continue
            while True:
                r = bot.SendMessage('group',g.id,soup.Forward(*node))
                if r.messageId and r.messageId == -1:fwimg2qr(node)
                elif r.code == 20 or r.code == 30:break
                elif r.messageId and r.messageId > 0:break
        pack.pop(f'{target}{Sender.id}')
        bot.SendMessage(Type,target,soup.Plain(Plain))

    if f'{target}{Sender.id}' in pack:
        pack[f'{target}{Sender.id}'].append(msgClear(Message))

    if Plain in ('打包开始','开始打包') and Sender.id in admin_ID(True,True) and f'{target}{Sender.id}' not in pack:
        pack[f'{target}{Sender.id}'] = []
        bot.SendMessage(Type,target,soup.Plain(Plain))