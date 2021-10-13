# -*- coding: utf-8 -*-

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
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
        if msg.type == 'Plain':
            msg = msg.text
            break
    for r in ['setu','色图','涩图']:
        if r in msg:
            msg = msg.replace(r, '')
            break
    else:return
    for r in ['r18', 'R18', 'r-18', 'R-18']:
        if r in msg:
            msg = msg.replace(r, '')
            r = 1
            break
    else:r = 0
    try:num = int(msg)
    except:num = 1
    else:num = (num > 30 and 30) or (num < 1 and 1) or num
    j = setu(r, num)
    if j['error'] != '':
        bot.SendMessage(Type, target, soup.Plain(j['error']))
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
                bot.SendMessage(Type, target, soup.Xml(xml))
            else:
                bot.SendMessage(Type, target, soup.Plain('r18每5分钟刷新重置'))

    else:
        _n = '\n'
        if len(j) > 1:
            node = []
            for i in j:
                Plain = f'标题:{i["title"]} Pid:{i["pid"]}{_n}作者:{i["author"]} Uid:{i["uid"]}{_n}标签:'
                for tag in i['tags']:Plain += tag + ' '
                node.append(soup.Node(bot.conf.qq,'robot',soup.Plain(Plain),soup.Image(url=i['urls']['original'])))
            bot.SendMessage(Type, target, soup.Forward(*node))
        else:
            Plain = f'标题:{j[0]["title"]} Pid:{j[0]["pid"]}{_n}作者:{j[0]["author"]} Uid:{j[0]["uid"]}{_n}标签:'
            for tag in j[0]['tags']:Plain += tag + ' '
            bot.SendMessage(Type, target, soup.Plain(Plain), soup.Image(url=j[0]['urls']['original']))