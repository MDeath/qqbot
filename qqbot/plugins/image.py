# -*- coding: utf-8 -*-

import time,traceback

from PicImageSearch.sync import Ascii2D as Ascii2DSync
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
    bot.ascii = Ascii2DSync()

def onUnplug(bot):
    del bot.sauce
    del bot.ascii

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复图片发送 '搜图' 可图片溯源'''
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
    if Plain.strip()!='搜图':return
    Image = []
    for msg in Message:
        if msg.type == 'Image':Image.append(msg)
        elif msg.type == 'Quote':
            code, msg = bot.MessageId(target,msg.id)
            if not code:
                Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
            else:
                for n in range(Source.id-1,Source.id-11,-1):
                    code, msg = bot.MessageId(target,n)
                    if not code:
                        Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
                        break
                else:
                    bot.SendMessage(Type, target, soup.Plain('⚠️关联图片失败，请尝试直接和图片一起发送⚠️'), id=Source.id)
                    return
    if not Image:
        bot.SendMessage(Type, target, soup.Plain('⚠️没有关联图片，请尝试直接和图片一起发送⚠️'), id=Source.id)
        return
    for img in Image:
        error_nember = 0
        while True:
            try:
                results = bot.sauce.from_url(img.url) # or from_file()
                break
            except UnknownApiError:
                WARNING('搜图失败，请稍后尝试')
            except LongLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain('🚫今日已达上限，请到明日尝试🚫'), id=Source.id)
                return
            except ShortLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain('⛔搜图进入CD，请等候30秒⛔'), id=Source.id)
                time.sleep(30)
            except Exception as e:
                ERROR(f"Count:{error_nember} ERROR:{e}")
                if error_nember == 5:bot.SendMessage(Type, target, soup.Plain('🆘暂时无法连到服务器，请联系管理员🆘'), id=Source.id)
            error_nember += 1

        pid = False
        message = []
        if results:
            message.append(soup.Plain(f'有 {len(results)} 个结果'))
            bot.SendMessage(Type, target, soup.Plain('正在搜图♾️'), id=Source.id)
            INFO(results)
        else:
            bot.SendMessage(Type, target, soup.Plain('⚠️搜图失败，请稍后尝试⚠️'))
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
        if max([r.similarity for r in results]) < 60:
            try:
                resp = bot.ascii.search(img.url) # 色相
                for r in resp:
                    if r.title or r.url_list:
                        message.append(soup.Plain('色相搜索：'))
                        if r.title:
                            message.append(f'\ntitle:{r.title}')
                        message.append(soup.Image(r.thumbnail))
                        if r.url_list:
                            message.append(soup.Plain('\n'.join([f'{v}:{k}' for k,v in r.url_list])))
                        break
                
                resp = bot.ascii.search(img.url, bovw=True) # 特征
                for r in resp:
                    if r.title or r.url_list:
                        message.append(soup.Plain('特征搜索：'))
                        if r.title:
                            message.append(f'\ntitle:{r.title}')
                        message.append(soup.Image(r.thumbnail))
                        if r.url_list:
                            message.append(soup.Plain('\n'.join([f'{v}:{k}' for k,v in r.url_list])))
                        break
            except:
                traceback.print_exc()
            message.append(soup.Plain('\n⚠️⚠️⚠️匹配度较低，可能被裁切、拼接，或是 AI 作图⚠️⚠️⚠️'))
            
        bot.SendMessage(Type, target, *message, id=Source.id)
        if pid:
            bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{pid}')])

        time.sleep(20)