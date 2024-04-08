# -*- coding: utf-8 -*-

from .saucenao_api import SauceNao
from .errors import UnknownApiError,LongLimitReachedError,ShortLimitReachedError

from .asc2d import Ascii2DSearch
# from PicImageSearch.sync import Ascii2D as Ascii2DSync

import os, re, time, traceback
from common import jsonload
import soup
from qqbotcls import bot
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from admin import admin_ID
from qr import fwimg2qr, img2qr

pid_black_list:int = [24704630]

class TokenError(Exception):pass

if os.path.exists(bot.conf.Config('saucenao.json')):
    with open(bot.conf.Config('saucenao.json'), 'r') as f:
        api_key = jsonload(f)
else:
    with open(bot.conf.Config('saucenao.json'), 'w') as f:
        f.write('[]')
    raise TokenError(f"Check the accesstoken in {bot.conf.Config('saucenao.json')}")

def pixivid(pid:str):
    pid = re.findall(r'\d+',pid)
    if not hasattr(bot,'pixiv') and not pid:return False
    pid = pid[-1]
    illust = bot.pixiv.illust_detail(pid)
    return False if 'error' in illust or not (illust.illust.title or illust.illust.user.name) else pid

def sauce(url):
    api_key.insert(0,api_key.pop())
    return SauceNao(api_key[0]).from_url(url)

def Resp2Msg(Type,Resp,pid):
    msg = []
    if len(Resp.raw) <= 1:return msg,pid
    for r in Resp.raw[1:]:
        msg.append([soup.Image(r.thumbnail)])
        if not (r.title or r.url_list):
            msg[-1].append(soup.Plain('暂无收录'))
            continue
        msg[-1].append(soup.Plain(f'\n{Type}搜索：\n标题：{r.title}' if r.title else f'\n{Type}搜索：'))
        if r.url_list:
            urls = ''
            for url,title in r.url_list:
                if pid is None and 'fanbox' not in url and any(u in url for u in ['www.pixiv.net/artworks','i.pximg.net']):
                    pid = pixivid(url)
                host = re.search(r"://.*?/",url)
                urls += f'\n{title}：\n{url.replace(host.group(),host.group().replace(".","。"))}' if host else f'\n{title}：\n{url}'
            msg[-1].append(soup.Plain(urls))
        if r.title and r.url_list:return msg,pid

def onPlug(bot):
    bot.sauce = sauce
    bot.ascii = Ascii2DSearch

def onUnplug(bot):
    del bot.sauce
    del bot.ascii

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复图片发送 '搜图' 可图片溯源
    回复图片发送 '识图' 可图片溯源，并自动获取PixivID'''
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = Sender.id, Sender.group.id

    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
    if Plain.strip() not in ['搜图', '识图']:return
    for msg in Message:
        if msg.type == 'Image':
            Image.append(msg)
        elif msg.type == 'Quote':
            r = bot.MessageId(target,msg.id)
            if not r.code:
                Message += [m for m in r.data.messageChain if m.type in ['Image','FlashImage']]
    if not Image:
        bot.SendMessage(Type, target, soup.Plain('⚠️关联图片失败，请尝试直接和图片一起发送，或是使用旧版客户端⚠️'), id=Source.id)
        return
    bot.SendMessage(Type, target, soup.Plain(f'正在{Plain.strip()}♾️'), id=Source.id)
    for img in Image:
        pid = None if Plain.strip()=='识图' else False
        message = [soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Image(img.url),soup.Plain('\n识别结果：'))]

        error_number = 0
        while True:
            try:
                if Type!="Friend":
                    try:ColorResp, BovwResp = Ascii2DSearch(img.url) # 色相，特征
                    except:ColorResp, BovwResp = None, None
                else:
                    try:ColorResp, BovwResp = Ascii2DSearch(img.url.replace(f'c2cpicdw.qpic.cn/offpic_new/{Sender.id}//',f'gchat.qpic.cn/gchatpic_new/0/').replace('c2cpicdw.qpic.cn/offpic_new/0//',f'gchat.qpic.cn/gchatpic_new/0/'))
                    except:ColorResp, BovwResp = None, None
                results = sauce(img.url) # or from_file()
                for n in range(len(results)):
                    r = results[n]
                    if ColorResp and (n == len([r.similarity for r in results if r.similarity >= 60]) or n == len(results)-1):
                        node, pid = Resp2Msg('特征',BovwResp,pid)
                        for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))
                        node, pid = Resp2Msg('色相',ColorResp,pid)
                        for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))

                    urls = ''
                    if 'source' in r.raw['data']:
                        host = re.search(r'://.*?/',r.raw['data']['source'])
                        urls += '\n' + (r.raw['data']['source'].replace(host.group(),host.group().replace('.','。')) if host else r.raw['data']['source'])

                    for url in r.urls:
                        host = re.search(r'://.*?/',url)
                        urls += '\n' + (url.replace(host.group(),host.group().replace('.','。')) if host else url)

                    s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}{urls}'

                    if pid is None and 'source' in r.raw['data'] and r.similarity >= 50:
                        if 'fanbox' not in r.raw['data']['source'] and any(u in r.raw['data']['source'] for u in ['www.pixiv.net','i.pximg.net']):
                            pid = pixivid(r.raw['data']['source'])

                    elif pid is None and r.similarity >= 55:
                        for url in r.urls:
                            if 'fanbox' not in url and any(u in url for u in ['www.pixiv.net','i.pximg.net']):
                                pid = pixivid(url)
                                if pid:break

                    message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Image(r.thumbnail),soup.Plain(s)))
                break
            except UnknownApiError as e:
                if error_number == 5 and not message:
                    bot.SendMessage(Type, target, soup.Plain('⚠️搜图失败，请稍后尝试⚠️'), id=Source.id)
                WARNING(e)
            except LongLimitReachedError:
                if not message:bot.SendMessage(Type, target, soup.Plain('🚫今日已达上限，搜索结果受限🚫'), id=Source.id)
                results = None
                break
            except ShortLimitReachedError:
                if not message:bot.SendMessage(Type, target, soup.Plain('⛔搜图进入CD，请等候30秒⛔'), id=Source.id)
                time.sleep(30)
            except:
                ERROR(f"Count:{error_number} ERROR:{traceback.format_exc()}")
            if error_number == 5 and not message:
                break
            error_number += 1

        if not message:
            bot.SendMessage(Type, target, soup.Plain('🆘暂时无法连到服务器🆘'), id=Source.id)
            results = None
            return

        error_number = 0
        while True:
            r = bot.SendMessage(Type, target, soup.Forward(*message,summary=f'查看{len(message)}条查询结果',preview=['⚠️匹配度较低，可能被裁切、拼接，或是AI作图⚠️'] if results and max([r.similarity for r in results]) < 60 else None))
            error_number += 1
            if r.messageId == -1:
                if error_number == 1:message[0]['messageChain'][0] = img2qr(img.url, img.url)
                if error_number == 2:fwimg2qr(message)
            elif not r.code:break
            elif r.code == 20:break
            elif r.code == 500:pass
            if error_number == 3:
                for n in message:
                    for m in range(len(n.messageChain)):
                        if n.messageChain[m].type == 'Image':
                            n.messageChain[m] = soup.Plain('[被吞]')
            if error_number == 4:
                bot.SendMessage(Type, target, soup.Plain('🆘发送失败🆘'),id=Source.id)
                break
        if pid and int(pid) not in pid_black_list:
            bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{pid}')])

        time.sleep(20)
