# -*- coding: utf-8 -*-

from __saucenao_api import SauceNao
import soup
from mainloop import Put

api_key = 'bb8c58baab8a50ab362c752b9f4252147c376da9'

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
        elif msg.type == 'Quote':
            quote = msg.id
            Quote = bot.MessageFromId(quote)
            if Quote:
                Message += Quote.messageChain
    if not Image:return
    
    if Plain.replace(' ','').replace('\n','') == '搜图':
        for img in Image:
            # Replace the key with your own
            sauce = SauceNao(api_key)
            results = sauce.from_url(img.url) # or from_file()
            message = []
            if results:
                message.append(soup.Plain(f'有 {len(results)} 个结果'))
                for r in results:
                    urls = ''
                    for url in r.urls:urls+='\n'+url
                    if r.similarity > 50:
                        message.append(soup.Plain(
                            f'\n相似度：{r.similarity}\n标题：{r.title}\n作者：{r.author}\nurl：{urls}'
                        ))
                    else:
                        message.append(soup.Plain(
                            f'\n相似度：{r.similarity}\nurl：{urls}'
                        ))
                bot.SendMessage(Type, target, *message, quote=quote)