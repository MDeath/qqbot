# -*- coding: utf-8 -*-

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
import re
import requests

import __soup as soup
from common import BYTES2STR, JsonLoads

image = '''
<msg serviceID="1" templateID="0" action="web" brief="" sourceMsgId="0" url="" flag="8" adverSign="0" multiMsgFlag="0">
    <item layout="2" advertiser_id="0" aid="0">
        <picture cover=""/>
        <title color="#777777"></title>
        <summary></summary>
    </item>
    <source name="pixiv" icon="" action="" appid="-1" />
</msg>'''


def setu(r=0, num=1, uid=[], tag=[], size=[]):
    payload = {'r18': r}
    payload['num'] = num
    if uid:
        payload['uid'] = uid
    if tag:
        payload['tag'] = tag
    if size:
        payload['size'] = size
    return JsonLoads(requests.get('https://api.lolicon.app/setu/v2', params=payload).text)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 setu 返回图片
    可添加数字规定数量
    可添加 r-18 关键字'''
    if Type not in ['Friend', 'Group']:return
    if hasattr(Sender, 'group'):target = Sender.group.id
    else:target = Sender.id
    for msg in Message:
        if msg.type == 'Plain' and 'setu' in msg.text:
            message = msg.text.replace('setu', '')
            break
    else:return
    for r in ['r18', 'R18', 'r-18', 'R-18']:
        if r in message:
            message = message.replace(r, '')
            r = 1
            break
    else:r = 0
    try:num = int(message)
    except:num = 1
    else:num = (num > 30 and 30) or (num < 1 and 1) or num
    j = setu(r, num)
    if j['error'] != '':
        bot.SendMessage(Type, target, [soup.Plain(j['error'])])
        return
    j = j['data']
    if r:
        i = j[0]
        xml = ET.fromstring(image)
        xml.set('brief', i['title'])
        xml.set('url', i['urls']['original'])
        for item in xml.iter('item'):
            for picture in item.iter('picture'):
                picture.set('cover', i['urls']['original'])
            for title in item.iter('title'):
                title.text = i['title']
            for summary in item.iter('summary'):
                summary.text = i['author'] + '\n'
                for tag in i['tags']:
                    summary.text += ','+tag
        xml = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>" + \
            BYTES2STR(ET.tostring(xml))
        # 群限制
        if hasattr(Sender, 'group'):
            if hasattr(bot, 'xml') and bot.xml > 0:
                bot.xml -= 1
            else:
                bot.SendMessage(Type, target, [soup.Plain('xml 群消息达上限')])
                return

        bot.SendMessage(Type, target, [soup.Xml(xml)])
    else:
        _n = '\n'
        for i in j:
            Plain = f'标题:{i["title"]} Pid:{i["pid"]}{_n}作者:{i["author"]} Uid:{i["uid"]}{_n}标签:'
            for tag in i['tags']:Plain += tag + ' '
            message = [soup.Plain(Plain), soup.Image(url=i['urls']['original'])]
            print(type(message),message)
            bot.SendMessage(Type, target, message)
