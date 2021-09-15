# -*- coding: utf-8 -*-

import json
from random import randint
from __soup import Plain
from os.path import exists

root = []
def onPlug(bot):
    if not hasattr(bot, 'facemap'):
        try:
            if exists(bot.conf.Config('facemap.json')):
                with open(bot.conf.Config('facemap.json'), 'r', encoding='utf-8') as f:
                    Map = json.load(f)
            else:raise
        except:
            with open(bot.conf.Config('facemap.json'),'w', encoding='utf-8') as f:
                json.dump(root, f, ensure_ascii=False, indent=4)
            Map = root.copy()
        if hasattr(bot, 'facemap'):
            bot.facemap.update(Map)
        else:
            setattr(bot, 'facemap', Map)

def onUnplug(bot):
    if hasattr(bot, 'facemap'):
        with open(bot.conf.Config('facemap.json'),'w', encoding='utf-8') as f:
                json.dump(bot.facemap, f, ensure_ascii=False, indent=4)
        delattr(bot, 'facemap')

def onInterval(bot):
    if hasattr(bot, 'facemap'):
        with open(bot.conf.Config('facemap.json'),'w', encoding='utf-8') as f:
                json.dump(bot.facemap, f, ensure_ascii=False, indent=4)

def onQQMessage(bot, Type, Sender, Source, Message):
    r'自动触发表情包'
    if not hasattr(bot,'facemap'):return
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    for msg in Message:
        if msg.type == 'Quote':
            quote = msg.id
            Quote = bot.MessageFromId(quote)
            if not Quote:return
            Message = Quote.messageChain + Message
            break
    message = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':
            message += msg.text
        if msg.type == 'Image':
            Image.append(msg)
    if not message.startswith('表情包'):
        for d in bot.facemap:
            for t in d['text']:
                if t in message and randint(0,1):
                    bot.SendMessage(Type,target,[d['image'][randint(1,len(d['image']))-1]])
        return
    message = message.replace('表情包','',1)
    if message.startswith('移出'):
        message = message.replace('移出','',1)
        Dn = 0
        for d in bot.facemap:
            if message in d['text']:
                Tn = 0
                for t in d['text']:
                    if message == t:
                        break
                    Tn += 1
                In = 0
                if Image:
                    for image in Image:
                        for i in d['image']:
                            if image['imageId'] == i['imageId']:
                                del d['image'][In]
                                bot.SendMessage(Type,target,[Plain(f'已从关键字 {message} 中移除此图'),image])
                                break
                            In += 1
                        else:
                            bot.SendMessage(Type,target,[Plain(f'关键字 {message} 中不存在此图'),image])
                else:
                    del d['text'][Tn]
                    bot.SendMessage(Type,target,[Plain(f'已移除关键字 {message}')])
                if not d['text'] or not d['image']:del bot.facemap[Dn]
                break
            Dn += 1
        else:
            bot.SendMessage(Type,target,[Plain(f'没有相关关键字 {message}')])
    elif message.startswith('查看'):
        message = message.replace('查看','',1)
        for d in bot.facemap:
            if message in d['text']:
                bot.SendMessage(Type,target,[Plain(json.dumps(d,ensure_ascii=False,indent=4))])
                break
        else:
            bot.SendMessage(Type,target,[Plain(f'没有相关关键字 {message}')])
    elif message.startswith('='):
        message = message.replace('=','',1)
        if not Image:
            bot.SendMessage(Type,target,[Plain('没有附带图片')])
            return
        for d in bot.facemap:
            if message in d['text']:
                for image in Image:
                    for i in d['image']:
                        if i['imageId'] == image['imageId']:
                            bot.SendMessage(Type,target,[Plain(f'关键字 {message} 已有此图'),image])
                            break
                    else:
                        d['image'].append(image)
                        bot.SendMessage(Type,target,[Plain(f'关键字 {message} 已添加此图'),image])
                break
        else:
            bot.facemap.append({'text':[message],'image':[image for image in Image]})
            bot.SendMessage(Type,target,[Plain(f'已创建关键字 {message}')])
    elif '=' in message:
        text = message.split('=',1)
        for d in bot.facemap:
            if text[0] in d['text'] or text[1] in d['text']:
                d['text'] = list(set(d['text'] + text))
                bot.SendMessage(Type,target,[Plain(f'已关联关键字 {message}')])
                break
        else:
            bot.SendMessage(Type,target,[Plain(f'没有相关关键字 {message}')])