from common import JsonLoads

from __soup import Plain, Json

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复 json卡片 发送 解析json或json解析 返回 json源码
    回复 json源码 发送 json 返回 json卡片'''
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    for msg in Message:
        if msg.type == 'Plain' and msg.text in ['json','解析json','json解析']:
            message = msg.text
            break
    else:
        return
    for msg in Message:
        if msg.type == 'Quote':
            quote = msg.id
            Quote = bot.MessageFromId(quote)
            break
    else:
        return
    if 'json' == message and quote:
        for msg in Quote.messageChain:
            if msg.type == 'Plain':
                msg = msg.text
                break
        else:
            return
        try:
            JsonLoads(msg)
        except:
            bot.SendMessage(Type, target, [Plain('json 格式有误')])
        else:
            bot.SendMessage(Type, target, [Json(msg)])
    elif quote:
        for msg in Quote.messageChain:
            if msg.type == 'json':
                json = msg.json
                break
        else:
            return
        json = json.replace('\\\\', '\\')
        json = json.replace('\\\'','\'')
        json = json.replace('\\\"','\"')
        try:
            JsonLoads(json)
        except:
            bot.SendMessage(Type, target, [Plain('消息不是 json 类型')])
        else:
            bot.SendMessage(Type, target, [Plain(json)])
    elif not quote:
        bot.SendMessage(Type, target, [Plain('没有引用 json')])