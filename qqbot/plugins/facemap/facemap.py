import json
from __soup import Plain
from common import JsonLoads, mydump
from os.path import exists
root = [
    {
        'text':[],
        'image':[]
    }
]

def onPlug(bot):
    if not hasattr(bot, 'facemap'):
        if exists('facemap.json'):
            with open('facemap.json', 'r') as f:Map = JsonLoads(f.read())
        else:
            mydump('facemap.json', root)
            Map = root.copy()
        setattr(bot, 'facemap', Map)
        for f in bot.Friend:
            if f.remark == 'Admin':
                target = f.id
        bot.SendMessage('Friend', target, [json.dumps(bot.facemap, ensure_ascii=False, indent=4)])

def onUnplug(bot):
    if hasattr(bot, 'facemap'):
        mydump('facemap.json', bot.facemap)
        delattr(bot, 'facemap')
'''
def onQQMessage(bot, Type, Sender, Source, Message):
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    for msg in Message:
        if msg.type == 'Plain' and 'diotu' in msg.text:
            message = msg.text
            message = message.replace('diotu', '')
            break
    else:
        return
    for msg in Message:
        if msg.type == 'Quote':
            quote = msg.id
            Quote = bot.MessageFromId(quote)
            break
    else:
        return'''