# -*- coding: utf-8 -*-

import time

import soup,common

def onPlug(bot):
    for g in bot.Group:
        setattr(g, 'time', 0)
        
def onUnplug(bot):
    for g in bot.Group:
        delattr(g, 'time')

def onInterval(bot):
    for g in bot.Group:
        if getattr(bot, 'time', 0) >= 60:
            bot.onQQMessage(
                'Group', 
                common.JsonDict({
                    'id': bot.conf.qq, 
                    'memberName': 'robot', 
                    'specialTitle': '', 
                    'permission': 'OWNER', 
                    'joinTimestamp': int(time.time()), 
                    'lastSpeakTimestamp': int(time.time()), 
                    'muteTimeRemaining': 0, 
                    'group': {
                        'id': g.id, 
                        'name': g.name, 
                        'permission': g.permission
                    }
                }), 
                common.JsonDict({
                    'type': 'Source', 
                    'id': 3609, 
                    'time': 1640396998
                }),
                [soup.Plain('setur18')]
            )

def onQQMessage(bot, Type, Sender, Source, Message):
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id