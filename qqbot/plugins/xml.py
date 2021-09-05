try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET

from __soup import Plain, Xml

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复 xml卡片 发送 xml 返回 xml源码
    发送 xml源码 返回 xml卡片'''
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    for msg in Message:
        if msg.type == 'Plain' and 'xml' in msg.text:
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
    if not Quote:return
    if "?xml" in message:
        try:
            ET.fromstring(message)
        except:
            bot.SendMessage(Type, target, [Plain('xml 格式有误')])
        else:
            bot.SendMessage(Type, target, [Xml(message)])
    elif 'xml' == message and quote:
        for msg in Quote.messageChain:
            if msg.type == 'Xml':
                xml = msg.xml
                break
        else:
            return
        xml = xml.replace('\\\\', '\\')
        xml = xml.replace('\\\'','\'')
        xml = xml.replace('\\\"','\"')
        try:
            ET.fromstring(xml)
        except:
            bot.SendMessage(Type, target, [Plain('消息不是 xml 类型')])
        else:
            bot.SendMessage(Type, target, [Plain(xml)])