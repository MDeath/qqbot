# -*- coding: utf-8 -*-

import re
import time, traceback

from plugins.admin import admin_ID
from pixivpy3 import *
import __soup as soup
from qqbotcls import QQBotSched

USERNAME = None
PASSWORD = None
REFRESH_TOKEN = 'HE7649-uwJxUXSjqYv82-gxvr5l9hlAdT1ol3lC-Ul0'

class Pixiv(ByPassSniApi):
    def __init__(self,**requests_kwargs): #初始化api
        super().__init__(**requests_kwargs)
        self.cat = False
        self.set_accept_language('zh-cn')
        self.require_appapi_hosts(hostname="public-api.secure.pixiv.net")

    def download(self, url, *args, **kwargs): #下载文件返回文件名
        if self.cat:
            url = url.replace('pximg.net', 'pixiv.cat')
        super().download(url,*args, **kwargs)

    def no_auth_requests_call(self, *args, **kwargs):
        while True:
            try:
                r = super().no_auth_requests_call(*args, **kwargs)
            except:
                traceback.print_exc()
                continue
            jsondict = self.parse_json(r.text)
            if 'error' not in jsondict:return r
            if 'Error occurred at the OAuth process.' in jsondict.error.message:
                print(jsondict.error.message)
                self.auth(refresh_token=self.refresh_token)
            else:
                print(jsondict.error.message)
                raise

def onPlug(bot):
    api = Pixiv()
    try:
        if REFRESH_TOKEN:
            api.auth(refresh_token=REFRESH_TOKEN)
        elif USERNAME and PASSWORD:
            api.login(USERNAME,PASSWORD)
        else:
            raise
        setattr(bot,'pixiv',api)
    except:raise

def onUnplug(bot):
    if hasattr(bot, 'pixiv'):
        del bot.pixiv

def onInterval(bot):
    if not hasattr(bot, 'pixiv'):
        onPlug(bot)
    bot.pixiv.auth(refresh_token=REFRESH_TOKEN)

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=6, 
            minute=None, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_ranking(bot):
    '''\
    每日凌晨6点发送pixiv日榜'''
    if not hasattr(bot, 'pixiv'):return
    api = bot.pixiv
    _n = '\n'
    n = 10
    result = api.illust_ranking()
    while n > 0:
        for i in result.illusts:
            if n < 1:break
            if i.type != 'illust':continue
            Plain = f'标题:{i.title} Pid:{i.id}{_n}作者:{i.user.name} Uid:{i.user.id}{_n}标签:'
            for tag in i.tags:Plain += f'{_n}{tag.name}:{tag.translated_name}'
            message = [soup.Plain(Plain)]
            if i.page_count > 1:
                for page in i.meta_pages:
                    message.append(soup.Image(url=page.image_urls.original.replace('pximg.net','pixiv.cat')))
            else:
                message.append(soup.Image(url=i.meta_single_page.original_image_url.replace('pximg.net','pixiv.cat')))
            for g in bot.Group:
                bot.SendMessage('Group', g.id, message)
            time.sleep(1)
            n -= 1
        if n > 0:
            result = api.illust_ranking(**api.parse_qs(result.next_url),req_auth=bot.pixiv.req_auth)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 推荐插画 或 插画推荐
    返回pixiv插画推荐（最多发30幅图）'''
    if not hasattr(bot, 'pixiv'):return
    api = bot.pixiv
    if Type not in ['Friend', 'Group']:
        return
    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id
    Plain,_n = '','\n'
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
    for msg in ['插画推荐','推荐插画']:
        if msg in Plain:
            try:
                number = int(Plain.replace(msg,''))
                if number > 30:number = 30
            except:
                number = 1
            illusts = api.illust_recommended().illusts
            while number > 0:
                number -= 1
                illust = illusts[number]
                Plain = f'标题:{illust.title} Pid:{illust.id}{_n}作者:{illust.user.name} Uid:{illust.user.id}{_n}收藏:{illust.total_bookmarks} 标签:'
                for tag in illust.tags:Plain += f'{_n}{tag.name}:{tag.translated_name}'
                message = [soup.Plain(Plain)]
                if illust.page_count > 1:
                    for page in illust.meta_pages:
                        message.append(soup.Image(url=page.image_urls.original.replace('pximg.net','pixiv.cat')))
                else:
                    message.append(soup.Image(url=illust.meta_single_page.original_image_url.replace('pximg.net','pixiv.cat')))
                bot.SendMessage(Type, target, message)
            return
