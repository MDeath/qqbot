# -*- coding: utf-8 -*-

from .saucenao_api import SauceNao
from .errors import UnknownApiError,LongLimitReachedError,ShortLimitReachedError

from .asc2d import Ascii2DSearch
# from PicImageSearch.sync import Ascii2D as Ascii2DSync

import os, time, traceback
from common import JsonLoad
import soup
from qqbotcls import bot
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from admin import admin_ID
from qr import fwimg2qr

class TokenError(Exception):pass

if os.path.exists(bot.conf.Config('saucenao.json')):
    with open(bot.conf.Config('saucenao.json'), 'r') as f:
        api_key = JsonLoad(f)
else:
    with open(bot.conf.Config('saucenao.json'), 'w') as f:
        f.write('[]')
    raise TokenError(f"Check the accesstoken in {bot.conf.Config('saucenao.json')}")

def pixivid(pid):
    if not hasattr(bot,'pixiv'):return False
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
        msg[-1].append(soup.Plain(f'\n{Type}搜索：\n标题：{r.title}\n' if r.title else f'\n{Type}搜索：\n'))
        if r.url_list:
            for url,v in r.url_list:
                if pid is None and 'fanbox' not in url and any(u in url for u in ['www.pixiv.net/artworks','i.pximg.net']):
                    pid = pixivid(url.split('/')[-1].split('=')[-1].split('_')[0])
            msg[-1].append(soup.Plain('\n'.join([f'{v} : {k.replace(".","。")}' for k,v in r.url_list])))
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
            code, msg = bot.MessageId(target,msg.id)
            if not code:
                Message += [m for m in msg.messageChain if m.type in ['Image','FlashImage']]
            else:
                bot.SendMessage(Type, target, soup.Plain('⚠️关联图片失败，请尝试直接和图片一起发送⚠️'), id=Source.id)
                return
    if not Image:
        bot.SendMessage(Type, target, soup.Plain('⚠️没有关联图片，请尝试直接和图片一起发送⚠️'), id=Source.id)
        return
    for img in Image:
        bot.SendMessage(Type, target, soup.Plain('正在搜图♾️'), id=Source.id)
        pid = None if Plain.strip()=='识图' else False
        message = []
           
        error_nember = 0
        while True:
            try:
                if Type!="Friend":ColorResp, BovwResp = Ascii2DSearch(img.url) # 色相，特征
                else:ColorResp, BovwResp = Ascii2DSearch(img.url.replace(f'c2cpicdw.qpic.cn/offpic_new/{Sender.id}//',f'gchat.qpic.cn/gchatpic_new/0/').replace('c2cpicdw.qpic.cn/offpic_new/0//',f'gchat.qpic.cn/gchatpic_new/0/'))
                results = sauce(img.url) # or from_file()
                for n in range(len(results)):
                    r = results[n]
                    if n == len([r.similarity for r in results if r.similarity >= 60]):
                        node, pid = Resp2Msg('特征',BovwResp,pid)
                        for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))
                        node, pid = Resp2Msg('色相',ColorResp,pid)
                        for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))

                    urls = ('source' in r.raw['data'] and '\n'+r.raw['data']['source']) or ''
                    urls+= '\n'+'\n'.join(r.urls)
                    urls = urls.replace(".",'。')
                    s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}{urls}'
                    if pid is None and 'source' in r.raw['data'] and r.similarity >= 50:
                        if 'fanbox' not in r.raw['data']['source'] and any(u in r.raw['data']['source'] for u in ['www.pixiv.net','i.pximg.net']):
                            pid = pixivid(r.raw['data']['source'].split('/')[-1].split('=')[-1].split('_')[0])
                    elif pid is None and r.similarity >= 55:
                        for url in r.urls:
                            if 'fanbox' not in url and any(u in url for u in ['www.pixiv.net','i.pximg.net']):
                                pid = pixivid(url.split('/')[-1].split('=')[-1].split('_')[0])
                                if pid:break
                    message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Image(r.thumbnail),soup.Plain(s)))
                break
            except UnknownApiError as e:
                if error_nember == 5 and not message:
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
                ERROR(f"Count:{error_nember} ERROR:{traceback.format_exc()}")
            if error_nember == 5 and not message:
                bot.SendMessage(Type, target, soup.Plain('🆘暂时无法连到服务器🆘'), id=Source.id)
                results = None
                break
            error_nember += 1

        if not message:
            node, pid = Resp2Msg('特征',BovwResp,pid)
            for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))
            node, pid = Resp2Msg('色相',ColorResp,pid)
            for msg in node:message.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*msg))
        
        error_number = 0
        while True:
            code, msgid = bot.SendMessage(Type, target, soup.Forward(*message,summary=f'查看{len(message)}条查询结果',preview=['⚠️匹配度较低，可能被裁切、拼接，或是AI作图⚠️'] if results and max([r.similarity for r in results]) < 60 else None))
            error_number += 1
            if msgid == -1:fwimg2qr(message)
            elif not code:break
            elif code == 20:break
            elif code == 500:pass
            if error_number == 3:
                bot.SendMessage(Type, target, soup.Plain('🆘发送失败🆘'),id=Source.id)
                break
        if pid:
            bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{pid}')])

        time.sleep(20)