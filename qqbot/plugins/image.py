# -*- coding: utf-8 -*-

import time

from __saucenao_api import SauceNao
from __saucenao_api.errors import UnknownApiError,LongLimitReachedError,ShortLimitReachedError
import soup
from utf8logger import INFO, WARNING, ERROR
from admin import admin_ID

api_key = [
    'bb8c58baab8a50ab362c752b9f4252147c376da9',
    'deec4846d5d11b5686a1a67edbb14757354ba66d'
]

def onPlug(bot):
    bot.sauce = SauceNao(api_key)

def onUnplug(bot):
    del bot.sauce

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复图片发送 '搜图' 可图片溯源'''
    if Type not in ['Friend','Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
        elif msg.type == 'Image':Image.append(msg)
        elif msg.type == 'Quote':
            msg = bot.MessageFromId(msg.id)
            if msg != '5':
                Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
            else:
                for n in range(Source.id-1,Source.id-11,-1):
                    msg = bot.MessageFromId(n)
                    if type(msg) is not str:
                        Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
    if Plain.strip()!='搜图':return
    if not Image:
        bot.SendMessage(Type, target, soup.Plain('没有关联图片，请尝试直接和图片一起发送'), id=Source.id)
        return
    for img in Image:
        while True:
            try:
                results = bot.sauce.from_url(img.url) # or from_file()
            except UnknownApiError:
                WARNING('搜图失败，请稍后尝试')
            except LongLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain('今日已达上限，请到明日尝试'), id=Source.id)
                return
            except ShortLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain('搜图进入CD，请30秒后尝试'), id=Source.id)
                return
            except Exception as e:ERROR(e)
            else:
                break

        pid = False
        message = []
        if results:
            message.append(soup.Plain(f'有 {len(results)} 个结果'))
            bot.SendMessage(Type, target, soup.Plain('正在搜图'), id=Source.id)
            INFO(results)
        else:
            bot.SendMessage(Type, target, soup.Plain('搜图失败，请稍后尝试'))
            continue
        for r in results:
            urls = ('source' in r.raw['data'] and '\n'+r.raw['data']['source']) or ''
            urls+= '\n'+'\n'.join(r.urls)
            for k,v in {':':'：','.':'。'}.items():
                urls = urls.replace(k,v)
            if r.similarity < 60:
                s = f'\n相似度：{r.similarity}\n标题：{r.title}{urls}'
            else:
                message.append(soup.Image(r.thumbnail))
                s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}{urls}'
                if not pid and 'source' in r.raw['data']:
                    if 'fanbox' not in r.raw['data']['source'] and 'pixiv' in bot.plugins and ('https://www.pixiv.net' in r.raw['data']['source'] or 'https://i.pximg.net' in r.raw['data']['source']):
                        pid = r.raw['data']['source'].split('/')[-1].split('=')[-1].split('_')[0]
                        illust = bot.pixiv.illust_detail(pid)
                        if 'error' in illust or not (illust.illust.title or illust.illust.user.name):pid = False
                    elif r.raw['data']['source'].startswith('http'):
                        for f in admin_ID():
                            bot.SendMessage('Friend', f, soup.Plain(r.raw))
                elif not pid:
                    for url in r.urls:
                        if 'fanbox' not in url and 'pixiv' in bot.plugins and ('https://www.pixiv.net' in url or 'https://i.pximg.net' in url):
                            pid = url.split('/')[-1].split('=')[-1].split('_')[0]
                            illust = bot.pixiv.illust_detail(pid)
                            if 'error' in illust or not (illust.illust.title or illust.illust.user.name):pid = False
                            else:break
            message.append(soup.Plain(s))
        if max([r.similarity for r in results]) < 60:message.append(soup.Plain('\n匹配度较低，可能被裁切、拼接，或是 AI 作图'))
        bot.SendMessage(Type, target, *message, id=Source.id)
        if pid:
            bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{pid}')])

        time.sleep(20)