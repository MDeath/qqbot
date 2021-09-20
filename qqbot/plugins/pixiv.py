# -*- coding: utf-8 -*-

import re
import time

from plugins.admin import admin_ID
from pixivpy3 import *
import __soup as soup
from qqbotcls import QQBotSched

USERNAME = None
PASSWORD = None
REFRESH_TOKEN = None

def onPlug(bot):
    if not hasattr(bot, 'pixiv'):
        api = ByPassSniApi()
        api.require_appapi_hosts(hostname="public-api.secure.pixiv.net")
        api.set_accept_language('zh-cn')
        setattr(bot,'pixiv',api)
        if REFRESH_TOKEN or (USERNAME and PASSWORD):
            bot.pixiv.auth(USERNAME, PASSWORD, REFRESH_TOKEN)
            setattr(bot.pixiv, 'req_auth', True)
        else:
            setattr(bot.pixiv, 'req_auth', False)

def onUnplug(bot):
    if hasattr(bot, 'pixiv'):
        delattr(bot, 'pixiv')

def onInterval(bot):
    if hasattr(bot, 'pixiv'):
        onPlug(bot)

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=4, 
            minute=None, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_ranking(bot):
    if not hasattr(bot, 'pixiv'):
        onPlug(bot)
    api = bot.pixiv
    _n = '\n'
    n = 10
    result = api.illust_ranking(req_auth=bot.pixiv.req_auth)
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