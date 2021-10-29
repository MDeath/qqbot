# -*- coding: utf-8 -*-

import json, os, requests, time, traceback
import urllib.parse as up

import soup
from common import BYTES2STR, JsonLoads
from utf8logger import WARNING
from plugins.admin import admin_ID
from pixivpy3 import ByPassSniApi
from qqbotcls import QQBotSched

<<<<<<< Updated upstream
_n = '\n'
cat = 'i.pixiv.cat'
re = 'i.pixiv.re'
moe = 'proxy.pixivel.moe'
=======
USERNAME = None
PASSWORD = None
REFRESH_TOKEN = 'HE7649-uwJxUXSjqYv82-gxvr5l9hlAdT1ol3lC-Ul0'
>>>>>>> Stashed changes

class Pixiv(ByPassSniApi):
    def __init__(self,**requests_kwargs): #初始化api
        super().__init__(**requests_kwargs)
        self.cat = False
        self.set_accept_language('zh-cn')
        self.require_appapi_hosts(hostname="public-api.secure.pixiv.net")

    def no_auth_requests_call(self, *args, **kwargs):
        while True:
            try:
                r = super().no_auth_requests_call(*args, **kwargs)
            except:
                WARNING(traceback.format_exc())
                continue
            if r.ok:return r
            jsondict = self.parse_json(r.text)
            if hasattr(jsondict.error,'user_message') and jsondict.error.user_message:
                if '该作品已被删除，或作品ID不存在。' in jsondict.error.user_message:
                    return r
            elif hasattr(jsondict.error,'message') and jsondict.error.message:
                if 'Rate Limit' in jsondict.error.message:
                    time.sleep(10)
                    continue
                elif 'Error occurred at the OAuth process.' in jsondict.error.message:
                    self.auth(refresh_token=self.refresh_token)
                    continue
            return r

def onPlug(bot): # 群限制用和登录pixiv
    if not hasattr(bot,'r18'):
        bot.r18 = {'limit':5,'offset':0,'viewed':set()}
    api = Pixiv()
    try:
        if os.path.exists(bot.conf.Config('pixiv.json')):
            with open(bot.conf.Config('pixiv.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:raise
    except:
        with open(bot.conf.Config('pixiv.json'),'w', encoding='utf-8') as f:
            json.dump({'REFRESH_TOKEN':'','USERNAME':'','PASSWORD':''}, f, ensure_ascii=False, indent=4)
            bot.Unplug(__name__)
    REFRESH_TOKEN = config['REFRESH_TOKEN']
    USERNAME = config['USERNAME']
    PASSWORD = config['PASSWORD']
    try:
        if REFRESH_TOKEN:
            api.auth(refresh_token=REFRESH_TOKEN)
        elif USERNAME and PASSWORD:
            api.login(USERNAME,PASSWORD)
        else:
            bot.Unplug(__name__)
        setattr(bot,'pixiv',api)
    except:raise

def onUnplug(bot):
    if hasattr(bot, 'pixiv'):
        del bot.pixiv

def onInterval(bot): # 刷新群限制和刷新令牌
    bot.r18['limit'] = 5
    bot.pixiv.auth()

@QQBotSched(hour=0)
def day_r18(bot):
    bot.r18['offset'] = 0

@QQBotSched(day_of_week=1)
def day_r18(bot):
    bot.r18['offset'] = 0

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
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    api:Pixiv = bot.pixiv
    n = 10
    result = api.illust_ranking()
    node = [soup.Node(bot.conf.qq,'robot',soup.Plain('Pixiv 每日榜'))]
    while n > 0:
        for i in result.illusts:
            if n < 1:break
            if i.type != 'illust':continue
            Plain = f'标题:{i.title} Pid:{i.id}{_n}作者:{i.user.name} Uid:{i.user.id}{_n}标签:'
            for tag in i.tags:Plain += f'{_n}{tag.name}:{tag.translated_name}'
            message = [soup.Plain(Plain)]
            if i.page_count > 1:
                for page in i.meta_pages:
                    message.append(soup.Image(url=page.image_urls.original.replace('i.pximg.net',moe)))
            else:
                message.append(soup.Image(url=i.meta_single_page.original_image_url.replace('i.pximg.net',moe)))
            node.append(soup.Node(bot.conf.qq,'robot',*message))
            n -= 1
        if n > 0:
            result = api.illust_ranking(**api.parse_qs(result.next_url))
    for g in bot.Group:
        while not bot.SendMessage('Group', g.id, soup.Forward(*node)):pass

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 '插画推荐','推荐插画','setu','色图','涩图'
    返回pixiv插画推荐（最多发15幅图）
    Pid Uid 查询'''
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    api:Pixiv = bot.pixiv
    if Type not in ['Friend', 'Group']:return
    if hasattr(Sender, 'group'):target = Sender.group.id
    else:target = Sender.id
    Plain = ''
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text

    for keyword in ['插画推荐','推荐插画','setu','色图','涩图']:
        if not Plain.startswith(keyword):continue
        Plain = Plain.replace(keyword,'')
        node = [soup.Node(Sender.id,None,soup.Plain(keyword))]
        for keyword in ['r18', 'R18', 'r-18', 'R-18']: # r18
            if keyword not in Plain:continue
            if bot.r18['limit'] < 1: # r18 限制
                bot.SendMessage(Type,target,soup.Plain('r18每5分钟刷新'))
                return
            bot.r18['limit'] -= 1
            for illust in api.illust_ranking('day_r18',offset=bot.r18['offset']).illusts:
                bot.r18['offset'] += 1
                if illust.id not in bot.r18['viewed']:
                    bot.r18['viewed'].add(illust.id)
                    break
            illusts = [illust]
            break
        else: # 正常推荐
            try:number = int(Plain)
            except:number = 1
            else:number = (number > 15 and 15) or (number < 1 and 1) or number
            illusts = api.illust_recommended().illusts[:number]
        for illust in illusts: # 合并发送
            Plain = f'标题:{illust.title} Pid:{illust.id}{_n}作者:{illust.user.name} Uid:{illust.user.id}{_n}类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:'
            for tag in illust.tags:Plain += f'{_n}{tag.name}:{tag.translated_name}'
            message = [soup.Plain(Plain)]
            if illust.page_count > 1:
                for page in illust.meta_pages:
                    message.append(soup.Image(url=page.image_urls.original.replace('i.pximg.net',moe)))
            else:
                message.append(soup.Image(url=illust.meta_single_page.original_image_url.replace('i.pximg.net',moe)))
            node.append(soup.Node(bot.conf.qq,'robot',*message))
        while not bot.SendMessage(Type, target, soup.Forward(*node)):pass
        return

    Plain = Plain.replace(' ','').replace(':','').replace('：','')
    if Plain.startswith(('pid','Pid','PID')):
        try:pid = int(Plain[3:])
        except:
            bot.SendMessage(Type,target,soup.Plain('例:PID12345678'))
            return
        illust = api.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in illust.error.items() if v]
            return
        illust = illust.illust
        Plain = f'标题:{illust.title} Pid:{illust.id}{_n}作者:{illust.user.name} Uid:{illust.user.id}{_n}类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:'
        for tag in illust.tags:Plain += f'{_n}{tag.name}:{tag.translated_name}'
        node = soup.Node(bot.conf.qq,'robot',soup.Plain(Plain)),
        if illust.page_count > 1:
            for page in illust.meta_pages:
                node += soup.Node(bot.conf.qq,'robot',soup.Image(url=page.image_urls.original.replace('i.pximg.net',moe))),
        else:
            node += soup.Node(bot.conf.qq,'robot',soup.Image(url=illust.meta_single_page.original_image_url.replace('i.pximg.net',moe))),
        while not bot.SendMessage(Type, target, soup.Forward(*node)):pass
        return

    if Plain.startswith(('uid','Uid','UID')):
        try:uid = int(Plain[3:])
        except:
            bot.SendMessage(Type,target,soup.Plain('例:UID12345678'))
            return
        user = api.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in user.error.items() if v]
            return
        message = soup.Image(user.user.profile_image_urls),
        message += soup.Plain(f"Pid:{user.user.id} 名字:{user.user.name}{_n} 插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        while not bot.SendMessage(Type,target,*message):pass