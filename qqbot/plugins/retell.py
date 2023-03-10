# -*- coding: utf-8 -*-

import random

def onPlug(bot):
    if not hasattr(bot,'retell'):bot.retell = {}

def onUnplug(bot):
    if hasattr(bot,'retell'):delattr(bot,'retell')

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    复读模块'''
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        return

    for msg in Message:
        if msg.type == 'Plain' and msg.text.startswith('你的QQ暂不支持查看'):return
        if msg.type == 'AtAll':return
        if msg.type == 'FlashImage':return
        if msg.type == 'Voice':return
        if msg.type == 'Xml':return
        if msg.type == 'Json':return
        if msg.type == 'App':return
        if msg.type == 'Poke':return 
        if msg.type == 'Dice':return
        if msg.type == 'MusicShare':return
        if msg.type == 'ForwardMessage':return 
        if msg.type == 'File':return

    if target not in bot.retell:bot.retell[target] = []
    bot.retell[target].append({'id':Sender.id,'msg':str(Message)})
    bot.retell[target] = bot.retell[target][-10:]

    # if random.randint(1,100) == 1: # 1% 概率自动复读
    #     bot.SendMessage(Type, target, *Message)
    #     bot.retell[target] = []
    #     return

    Sender_id = {log['id'] for log in bot.retell[target]}
    if len(Sender_id) < random.randint(1,10):return
    log = [log['msg'] for log in bot.retell[target]]
    if len(log) > random.randint(1,10) >= len(set(log)):
        Max = [1,None,0]
        for msg in log:
            if log.count(msg)>Max[0]:Max = [log.count(msg),msg,0]
            Max[2] += 1
        if Max[1] and random.randint(1,Max[2]) == Max[2]:
            bot.SendMessage(Type, target, *eval(Max[1]))
            bot.retell[target] = []