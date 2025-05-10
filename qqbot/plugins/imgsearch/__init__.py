# -*- coding: utf-8 -*-

from .saucenao_api import SauceNao
from .errors import UnknownApiError,LongLimitReachedError,ShortLimitReachedError,UnknownClientError

from .asc2d import Ascii2DSearch
# from PicImageSearch.sync import Ascii2D as Ascii2DSync

import os, re, time, traceback
from common import jsonload
import soup
from qqbotcls import bot
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from qr import imageType2qr, img2qr
from admin import admin_ID

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
    return pid[-1] if pid else False

def sauce(url):
    api_key.insert(0,api_key.pop())
    return SauceNao(api_key[0]).from_url(url)

def Resp2Msg(Type,Resp,pid,qr=False):
    msg = []
    if len(Resp.raw) <= 1:return msg,pid
    for r in Resp.raw[1:]:
        msg.append([soup.Image(r.thumbnail) if qr else img2qr(picture=r.thumbnail)])
        if not (r.title or r.url_list):
            msg[-1].append(soup.Text('暂无收录'))
            continue
        msg[-1].append(soup.Text(f'\n{Type}搜索：\n标题：{r.title}' if r.title else f'\n{Type}搜索：'))
        if r.url_list:
            urls = ''
            for url,title in r.url_list:
                if isinstance(pid,list) and 'fanbox' not in url and any(u in url for u in ['www.pixiv.net/artworks','i.pximg.net']):
                    pid.append(pixivid(url))
                host = re.search(r"://.*?/",url)
                urls += f'\n{title}：\n{url.replace(host.group(),host.group().replace(".","。"))}' if host else f'\n{title}：\n{url}'
            msg[-1].append(soup.Text(urls))
        if r.title and r.url_list:return msg,pid

def search(Type,Sender,Source,imgurl,pid):
    front = []
    message = []
    error_number = 0
    try:ColorResp, BovwResp = Ascii2DSearch(imgurl.replace(f'c2cpicdw.qpic.cn/offpic_new/{Sender.user_id}//',f'gchat.qpic.cn/gchatpic_new/0/').replace('c2cpicdw.qpic.cn/offpic_new/0//',f'gchat.qpic.cn/gchatpic_new/0/')) # 9.0 以前的图床转换
    except:ColorResp, BovwResp = None, None
    if ColorResp:
        for mode,Resp in [['特征',BovwResp],['色相',ColorResp]]:
            node, pid = Resp2Msg(mode,Resp,pid,Type=='friend')
            for n in node:message.append(soup.Node(*n,uid=Sender.user_id,nickname=Sender.nickname))
    while True:
        error_number += 1
        if 'offpic_new' in imgurl:imgurl = imgurl.replace('multimedia.nt.qq.com.cn','c2cpicdw.qpic.cn') # 9.0 以前的图床转换
        if 'gchatpic_new' in imgurl:imgurl = imgurl.replace('multimedia.nt.qq.com.cn','gchat.qpic.cn') # 9.0 以前的图床转换
        similarity = True
        try:
            results = sauce(imgurl) # or from_file()
            for r in results:
                urls = ''
                if 'source' in r.raw['data']:
                    host = re.search(r'://.*?/',r.raw['data']['source'])
                    urls += '\n' + (r.raw['data']['source'].replace(host.group(),host.group().replace('.','。')) if host else r.raw['data']['source'])

                for url in r.urls:
                    host = re.search(r'://.*?/',url)
                    urls += '\n' + (url.replace(host.group(),host.group().replace('.','。')) if host else url)

                s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}{urls}'

                if isinstance(pid,list) and 'source' in r.raw['data'] and r.similarity >= 55:
                    if 'fanbox' not in r.raw['data']['source'] and any(u in r.raw['data']['source'] for u in ['www.pixiv.net','i.pximg.net']):
                        pid.append(pixivid(r.raw['data']['source']))

                elif isinstance(pid,list) and r.similarity >= 55:
                    for url in r.urls:
                        if 'fanbox' not in url and any(u in url for u in ['www.pixiv.net','i.pximg.net']):
                            getpid = pixivid(url)
                            pid.append(getpid)
                            if getpid:break
                if r.similarity >= 60:
                    front.append(soup.Node(soup.Image(r.thumbnail) if Type == 'friend' else img2qr(picture=r.thumbnail),soup.Text(s),uid=Sender.user_id,nickname=Sender.nickname))
                else:
                    message.append(soup.Node(soup.Image(r.thumbnail) if Type == 'friend' else img2qr(picture=r.thumbnail),soup.Text(s),uid=Sender.user_id,nickname=Sender.nickname))
            similarity = r.similarity<60
            break
        except UnknownClientError as e:
            WARNING(e)
            bot.SendMsg(Type, Source.target, soup.Text('🆘搜图失败🆘'), reply=Source.message_id)
            if not front+message:return [], pid
        except UnknownApiError as e:
            WARNING(e)
            bot.SendMsg(Type, Source.target, soup.Text('⚠️搜图失败，请稍后尝试⚠️'), reply=Source.message_id)
            if not front+message:return [], pid
        except LongLimitReachedError:
            WARNING(f"Count:{error_number} ERROR:{traceback.format_exc()}")
            bot.SendMsg(Type, Source.target, soup.Text('🚫今日已达上限，搜索结果受限🚫'), reply=Source.message_id)
            if not front+message:return [], pid
        except ShortLimitReachedError:
            WARNING(f"Count:{error_number} ERROR:{traceback.format_exc()}")
            if not front+message:bot.SendMsg(Type, Source.target, soup.Text('⛔搜图进入CD，请等候30秒⛔'), reply=Source.message_id)
            time.sleep(30)
        except:ERROR(f"Count:{error_number} ERROR:{traceback.format_exc()}")
        if error_number == 5:
            bot.SendMsg(Type, Source.target, soup.Text('🆘搜图失败，请稍后尝试🆘'), reply=Source.message_id)
            if not front+message:return [], None
            break
    return [soup.Node(soup.Image(imgurl) if Type == 'friend' else img2qr(picture=imgurl),soup.Text(f'查看{len(front+message)}条查询结果:\n{"⚠️匹配度低可能是AI或裁切拼接⚠️" if similarity else ""}'),uid=Sender.user_id,nickname=Sender.nickname)]+front+message,pid

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
    Text = ''
    Image = set()
    for msg in Message:
        if msg.type == 'text':Text += msg.text
    if Text.strip() not in ['st', '搜图', '识图']:return
    for msg in Message:
        if msg.type == 'image':Image.add(msg.url)
        if msg.type == 'reply':
            try:[Image.add(m.url) for m in bot.GetMsg(msg.id).message if m.type == 'image']
            except:pass
    DEBUG(Message)
    if not Image:
        if Text.strip() != 'st':bot.SendMsg(Type, Source.target, soup.Text('⚠️关联图片失败，请尝试回复或与图片一起发送⚠️'), reply=Source.message_id)
        return
    
    if Type == 'group':bot.Reaction(Source.target,Source.message_id,424)
    else:bot.SendMsg(Type, Source.target, soup.Text(f'正在{Text.strip()}♾️'), reply=Source.message_id)

    for img in Image:
        pid = [] if Text.strip()=='识图' else False
        message, pid = search(Type, Sender, Source, img, pid)
        if len(message)==0:
            bot.SendMsg(Type, Source.target, soup.Text('🆘暂时无法连到服务器🆘'), reply=Source.message_id)
            continue

        error_number = 0
        while True:
            data = bot.SendMsg(Type, Source.target, *message)
            error_number += 1
            if 'retcode' not in data:break
            if error_number == 1:message.pop(0)
            if error_number == 2:imageType2qr(message)
            if error_number == 3:
                for n in message:
                    for m in n:
                        if m.type == 'image':
                            m.clear()
                            m.update(soup.Text('[被吞]'))
            if error_number == 4:
                data = bot.SendMsg(Type, Source.target, soup.Text('🆘发送失败🆘'),reply=Source.message_id)
                break
        for f in [f for f in admin_ID() if data.res_id and f.user_id != Source.target]:
            bot.SendMsg('friend', f.user_id, soup.Forward(data.res_id))
        if pid and hasattr(bot,'pixiv'):
            for i in pid[::-1]:
                illust = bot.pixiv.illust_detail(i)
                if 'error' in illust or not (illust.illust.title or illust.illust.user.name):continue
                if illust.illust.type == 'ugoira':
                    bot.SendMsg(Type, Source.target, soup.Text(f'♾️PixivID:{pid},Title:{illust.illust.title} 动图生成中♾️'), reply=Source.message_id)
                else:
                    bot.SendMsg(Type, Source.target, soup.Text(f'♾️PixivID:{pid},Title:{illust.illust.title} 获取中♾️'), reply=Source.message_id)
                bot.plugins.pixiv.send_illust(illust.illust, 'friend', Sender.user_id)
                break

        time.sleep(20)