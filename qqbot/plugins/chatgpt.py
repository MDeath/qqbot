# -*- coding: utf-8 -*-

import os, requests, traceback, time

from revChatGPT.V1 import Chatbot 

import soup
from qqbotcls import bot
from common import DotDict, JsonDump, JsonDumps, JsonDict
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING

class AccessTokenError(Exception):pass

if os.path.exists(bot.conf.Config('ChatGPT.token')):
    with open(bot.conf.Config('ChatGPT.token'), 'r') as f:
        access_token = f.read()
else:
    open(bot.conf.Config('ChatGPT.token'), 'w').close()
    raise AccessTokenError(f"Check the accesstoken in {bot.conf.Config('ChatGPT.token')}")

chatgpt = Chatbot(config={'access_token':access_token})
chatgpt.convo_list = []
while True:
    if len(chatgpt.convo_list) % 20 != 0:break
    chatgpt.convo_list += chatgpt.get_conversations()
chatgpt.run = False

def onPlug(bot):
    bot.chatgpt = chatgpt

def onUnplug(bot):
    del bot.chatgpt

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    AI模块对话模块使用 @ 开头 或 @Bot'''
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = [Sender.id, Sender.group.id]

    Plain = ''
    At = []
    for msg in Message:
        if msg.type == 'At':At.append(msg.target)
        if msg.type == 'Plain':Plain += msg.text

    if (not Plain.startswith('@') or len(Plain) < 2) and bot.conf.qq not in At:
        return
    if Plain.startswith('@'):
        Plain = Plain[1:]

    for convo in chatgpt.convo_list:
        if 'parent_id' not in convo:
            convo['parent_id'] = None
        if convo['title'] == str(target):
            break
    else:
        convo = {"id": None, 'title': str(target), 'parent_id': None}
        chatgpt.convo_list.append(convo)

    if Plain in ['清空','clear','cls']:
        if convo['id']:
            chatgpt.delete_conversation(convo['id'])
            convo['id'], convo['parent_id'] = None, None
        bot.SendMessage(Type, target, soup.Plain('🚮对话记录以清空☑'), id=Source.id)
        return

    if chatgpt.run:
        bot.SendMessage(Type, target, soup.Plain('对话进行中🤐请稍后再试'), id=Source.id)
        return
    chatgpt.run = True

    try:
        for data in chatgpt.ask(Plain, convo['id'], convo['parent_id'], auto_continue=True, timeout=9999):pass
    except:
        traceback.print_exc()
        bot.SendMessage(Type, target, soup.Plain('已达上限🥵稍后再试'), id=Source.id)
        
    chatgpt.run = False

    if 'message' not in data:
        ERROR(JsonDumps(Message, ensure_ascii=False, indent=4))
        bot.SendMessage(Type, target, soup.Plain('已达上限😵稍后再试'), id=Source.id)
        return
    if not convo['id']:
        chatgpt.change_title(data['conversation_id'], str(target))
    convo['id'] = data['conversation_id']
    convo['parent_id'] = data['parent_id']
    bot.SendMessage(Type, target, soup.Plain(data['message'].strip()), id=Source.id)