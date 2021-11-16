# -*- coding: utf-8 -*-

try:
  import xml.etree.cElementTree as ET
except ImportError:
  import xml.etree.ElementTree as ET

import re
import soup

# 群限制用
def onPlug(bot):
    if not hasattr(bot,'xml'):
        setattr(bot, 'xml', 5)

# 刷新群限制
def onInterval(bot):
    bot.xml = 5

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复 xml卡片 xml 返回 xml源码
    发送 xml源码 返回 xml卡片'''
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
            break
    for msg in Message:
        if msg.type == 'Plain' and 'xml' in msg.text:
            message = msg.text
            break
    else:
        return
    if '<?xml version=' in message:
        try:
            ET.fromstring(message)
        except:
            bot.SendMessage(Type, target, soup.Plain('xml 格式有误'))

        # 群限制
        if hasattr(Sender, 'group'):
            if hasattr(bot, 'xml') and bot.xml > 0:
                bot.xml -= 1
            else:
                bot.SendMessage(Type, target, soup.Plain('xml 群消息达上限'))
                return
        bot.SendMessage(Type, target, soup.Xml(message))
        
    elif 'xml' == message and Quote:
        for msg in Quote.messageChain:
            if msg.type == 'Xml':
                xml = msg.xml
                break
        else:
            bot.SendMessage(Type, target, soup.Plain('对象不是xml类型'))
            return
        xml = xml.replace('\\\\', '\\')
        xml = xml.replace('\\\'','\'')
        xml = xml.replace('\\\"','\"')
        try:
            ET.fromstring(xml)
        except:
            bot.SendMessage(Type, target, soup.Plain('消息不是 xml 类型'))
        else:
            bot.SendMessage(Type, target, soup.Plain(xml))