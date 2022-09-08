# -*- coding: utf-8 -*-

from __saucenao_api import SauceNao
import soup
from admin import admin_ID

api_key = 'bb8c58baab8a50ab362c752b9f4252147c376da9'

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
                Quote = bot.MessageFromId(msg.id)
            elif msg.id < 0:
                Quote = []
                for n in range(Source.id-1,Source.id-11,-1):
                    Quote += bot.MessageFromId(n)
            else:continue
            Message += Quote.messageChain
    
    if Plain.strip()=='搜图':
        if not Image:
            bot.SendMessage(Type, target, soup.Plain('没有关联图片，请尝试直接和图片一起发送'), id=Source.id)
            return
        for img in Image:
            # Replace the key with your own
            sauce:SauceNao = bot.sauce
            results = sauce.from_url(img.url) # or from_file()
            message = []
            if results:
                message.append(soup.Plain(f'有 {len(results)} 个结果'))
                for r in results:
                    urls = ('source' in r.raw['data'] and '\n'+r.raw['data']['source']) or ''
                    for url in r.urls:urls+='\n'+url
                    if r.similarity > 60:
                        message.append(soup.Image(r.thumbnail))
                        s = f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}\nurls：{urls}'
                        if r.urls and 'https://www.pixiv.net/' in r.urls[0] and 'pixiv'in bot.plugins and r.urls and 'fanbox' not in r.urls[0]:
                            ID = r.urls[0].split('=')[-1]
                            if 'error'not in bot.pixiv.illust_detail(ID):
                                bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{ID}')])
                                return
                        elif 'source' in r.raw['data']:
                            if 'fanbox' not in r.raw['data']['source'] and 'pixiv'in bot.plugins:
                                ID = 0
                                if 'https://www.pixiv.net' in r.raw['data']['source']:
                                    ID = r.raw['data']['source'].split('/')[-1]
                                elif 'https://i.pximg.net' in r.raw['data']['source']:
                                    ID = r.raw['data']['source'].split('/')[-1].split('_')[0]
                                if ID and 'error'not in bot.pixiv.illust_detail(ID):
                                    bot.onQQMessage(Type, Sender, Source, [soup.Plain(f'Pid{ID}')])
                                    return
                            elif r.raw['data']['source'].startswith('http'):
                                for f in admin_ID():
                                    bot.SendMessage('Friend', f, soup.Plain(r.raw))
                    else:
                        s = f'\n相似度：{r.similarity}\n标题：{r.title}\nurls：{urls}'
                    for k,v in ban.items():
                        s = s.replace(k,v)
                    message.append(soup.Plain(s))
                if max([r.similarity for r in results]) < 60:message.append(soup.Plain('\n匹配度较低，图片可能被裁切或者有拼接'))
                bot.SendMessage(Type, target, *message, id=quote)