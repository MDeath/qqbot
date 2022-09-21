# -*- coding: utf-8 -*-

from __saucenao_api import SauceNao
from __saucenao_api.errors import UnknownApiError,LongLimitReachedError,ShortLimitReachedError
import soup
from admin import admin_ID

api_key = [
    'bb8c58baab8a50ab362c752b9f4252147c376da9',
    'deec4846d5d11b5686a1a67edbb14757354ba66d'
]

ban = {
    'https://danbooru.donmai.us':'https://danbooru donmai us'
}

def onPlug(bot):
    bot.sauce = SauceNao(api_key)

def onUnplug(bot):
    del bot.sauce

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    回复 图片 发送 搜图 返回 图片溯源'''
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    quote = Source.id
    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
        if msg.type == 'Image':Image.append(msg)
        if msg.type == 'Quote':
            if msg.id > 0:
                Message += bot.MessageFromId(msg.id).messageChain
            elif msg.id < 0:
                for n in range(Source.id-1,Source.id-11,-1):
                    print(n)
                    Message += bot.MessageFromId(n).messageChain
            else:continue
    
    if Plain.strip()!='搜图':return
    if not Image:
        bot.SendMessage(Type, target, soup.Plain('没有关联图片，请尝试直接和图片一起发送'), id=Source.id)
        return
    for img in Image:
        while True:
            try:
                results = bot.sauce.from_url(img.url) # or from_file()
            except UnknownApiError:
                bot.SendMessage(Type, target, soup.Plain(f'搜图失败，请稍后尝试'))
            except LongLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain(f'今日已达上限，请到明日尝试'))
                return
            except ShortLimitReachedError:
                bot.SendMessage(Type, target, soup.Plain(f'搜图进入CD，请30秒后尝试'))
                return
            else:
                break

        pid = False
        message = []
        if results:
            message.append(soup.Plain(f'有 {len(results)} 个结果'))
        else:
            bot.SendMessage(Type, target, soup.Plain('搜图失败，请稍后尝试'))
            continue
        for r in results:
            urls = ('source' in r.raw['data'] and '\n'+r.raw['data']['source']) or '\n'+'\n'.join(r.urls)
            if r.similarity < 60:
                s = f'\n相似度：{r.similarity}\n标题：{r.title}{urls}'
            else:
                message.append(soup.Image(r.thumbnail))
                s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}{urls}'
                if 'source' in r.raw['data']:
                    if 'fanbox' not in r.raw['data']['source'] and 'pixiv' in bot.plugins and ('https://www.pixiv.net' in r.raw['data']['source'] or 'https://i.pximg.net' in r.raw['data']['source']):
                        pid = r.raw['data']['source'].split('/')[-1].split('=')[-1].split('_')[0]
                        if 'error' in bot.pixiv.illust_detail(pid):pid = False
                        else:break
                    elif r.raw['data']['source'].startswith('http'):
                        for f in admin_ID():
                            bot.SendMessage('Friend', f, soup.Plain(r.raw))
                else:
                    for url in r.urls:
                        if 'fanbox' not in url and 'pixiv' in bot.plugins and ('https://www.pixiv.net' in url or 'https://i.pximg.net' in url):
                            pid = url.split('/')[-1].split('=')[-1].split('_')[0]
                            if 'error' in bot.pixiv.illust_detail(pid):pid = False
                            else:break
                    if pid:break
            for k,v in ban.items():
                s = s.replace(k,v)
            message.append(soup.Plain(s))
        if pid:
            bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{pid}')])
        if max([r.similarity for r in results]) < 60:message.append(soup.Plain('\n匹配度较低，图片可能被裁切或者有拼接'))
        bot.SendMessage(Type, target, *message, id=quote)