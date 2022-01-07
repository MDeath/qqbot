# -*- coding: utf-8 -*-

import json, os, time, traceback, requests

import soup
from utf8logger import WARNING
from pixivpy3 import ByPassSniApi
from qqbotcls import QQBotSched

_n = '\n'
# 图片代理
hosts = {
    'cat' : 'i.pixiv.cat',
    're' : 'i.pixiv.re',
    'moe' : 'proxy.pixivel.moe',
    'a_f' : 'pixiv.a-f.workers.dev'
}
hosts = hosts['re']
# pixiv配置
config = {
    'hosts':None,
    'REFRESH_TOKEN':'',
    'USERNAME':'',
    'PASSWORD':''
}

class Pixiv(ByPassSniApi):
    def __init__(self,hosts=None,**requests_kwargs): #初始化api
        super().__init__(**requests_kwargs)
        self.set_accept_language('zh-cn')
        if hosts:self.hosts = hosts
        else:
            while not hasattr(self,'hosts'):
                try:self.require_appapi_hosts(hostname="public-api.secure.pixiv.net")
                except:pass

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

def illust_node(illusts, sendid=2854196310, name='QQ管家'):
    node = []
    for i in illusts:
        if i.type != 'illust':continue
        Plain = f'标题:{i.title} Pid:{i.id}{_n}作者:{i.user.name} Uid:{i.user.id}{_n}类型:{i.type} 收藏:{i.total_bookmarks} 标签:{_n}'
        for tag in i.tags:Plain += f'{tag.name}:{tag.translated_name}{_n}'
        message = [soup.Plain(Plain)]
        if i.page_count > 1:
            for page in i.meta_pages:
                message.append(soup.Image(url=page.image_urls.original.replace('i.pximg.net',hosts)))
        else:
            message.append(soup.Image(url=i.meta_single_page.original_image_url.replace('i.pximg.net',hosts)))
        node.append(soup.Node(sendid,name,*message))
    return node

def foldnode(node):
        top = node[0]
        for n in node:
            if len(top.messageChain) < len(n.messageChain):top = n
        msg = ''
        for n in top.messageChain[4:]:msg += f'{_n}{n.url}'
        msg += f'{_n}剩余 {len(top.messageChain[4:])} 张被折叠，请使用 pid 查询'
        top.messageChain[4] = soup.Plain(msg)
        top.messageChain = top.messageChain[:5]
        return node

def onPlug(bot): # 群限制用和登录pixiv
    if not hasattr(bot,'r18'):
        bot.r18 = {'offset':0,'viewed':[]}
        try:
            if os.path.exists(bot.conf.Config('R18.json')):
                with open(bot.conf.Config('R18.json'), 'r', encoding='utf-8') as f:bot.r18['viewed'] = json.load(f)
            else:raise
        except:
            with open(bot.conf.Config('R18.json'),'w', encoding='utf-8') as f:json.dump([], f, ensure_ascii=False, indent=4)
    try:
        if os.path.exists(bot.conf.Config('pixiv.json')):
            with open(bot.conf.Config('pixiv.json'), 'r', encoding='utf-8') as f:conf = json.load(f)
        else:raise
    except:
        with open(bot.conf.Config('pixiv.json'),'w', encoding='utf-8') as f:json.dump(config, f, ensure_ascii=False, indent=4)
        conf = config.copy()
    if conf['hosts']:
        bot.pixiv = Pixiv(conf['hosts'])
    else:
        bot.pixiv = Pixiv()
        conf['hosts'] = bot.pixiv.hosts
        with open(bot.conf.Config('pixiv.json'),'w', encoding='utf-8') as f:json.dump(conf, f, ensure_ascii=False, indent=4)
    try:
        if conf['REFRESH_TOKEN']:
            bot.pixiv.auth(refresh_token=conf['REFRESH_TOKEN'])
        elif conf['USERNAME'] and conf['PASSWORD']:
            bot.pixiv.login(conf['USERNAME'],conf['PASSWORD'])
        else:
            bot.Unplug(__name__)
    except:raise

def onUnplug(bot):
    del bot.pixiv

def onInterval(bot): # 刷新群限制和刷新令牌
    bot.pixiv.auth()
    with open(bot.conf.Config('R18.json'),'w', encoding='utf-8') as f:json.dump(bot.r18['viewed'], f)

@QQBotSched(hour=0)
def day_r18(bot):
    bot.r18['offset'] = 0

@QQBotSched(day_of_week=1)
def day_r18(bot):
    bot.r18['viewed'] = []

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
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking(mode='day')
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} 日榜单'))]
    node += illust_node(illusts.illusts[:10])
    for g in bot.Group:
        while True:
            code = bot.SendMessage('Group',g.id, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = foldnode(node)
            

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=0, 
            minute=None, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_r18_ranking(bot):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day_r18')
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv R18榜单'))]
    node += illust_node(illusts.illusts[:10])
    for f in bot.Friend:
        if f.remark != 'Admin' or f.nickname == 'Admin':continue
        while True:
            code = bot.SendMessage('Friend',f.id, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = foldnode(node)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 'setu','色图'或'涩图'(可指定数量)
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
        node = soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Plain(Plain)),
        if illust.page_count > 1:
            for page in illust.meta_pages:
                node += soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Image(url=page.image_urls.original.replace('i.pximg.net',hosts))),
        else:
            node += soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,soup.Image(url=illust.meta_single_page.original_image_url.replace('i.pximg.net',hosts))),
        error_number = 0
        for n in range(0,len(node),50):
            while True:
                code = bot.SendMessage(Type, target, soup.Forward(*node[n:n+50]))
                if error_number == 5:
                    bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),quote=Source.id)
                error_number += 1
                if type(code) is int:break
        return

    node = []
    if Plain.startswith(('uid','Uid','UID')):
        try:uid = int(Plain[3:])
        except:
            bot.SendMessage(Type,target,soup.Plain('例:UID12345678'))
            return
        user = api.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in user.error.items() if v]
            return
        message = soup.Image(user.user.profile_image_urls.medium.replace('i.pximg.net',hosts)),
        message += soup.Plain(f"Uid:{user.user.id} 名字:{user.user.name}{_n} 插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*message))
        illusts = api.user_illusts(user.user.id).illusts[:10]

    elif Plain.startswith(('setu','色图','涩图')):
        for kw in ['setu','色图','涩图']:Plain = Plain.replace(kw,'')
        if Plain.startswith(('r18', 'R18', 'r-18', 'R-18')): # r18
            for illust in api.illust_ranking('day_r18',offset=bot.r18['offset']).illusts:
                bot.r18['offset'] += 1
                if illust.id not in bot.r18['viewed']:
                    bot.r18['viewed'].append(illust.id)
                    break
            else:
                while True:
                    illust = api.illust_detail(requests.get('https://api.lolicon.app/setu/v2?r18=1').json()['data'][0]['pid'])
                    if 'error' not in illust:
                        illust = illust.illust
                        break
            illusts = [illust]
        else: # 正常推荐
            try:number = int(Plain)
            except:number = 1
            else:number = (number > 15 and 15) or (number < 1 and 1) or number
            illusts = api.illust_recommended().illusts[:number]
    else:return
    node += illust_node(illusts,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname)
    error_number = 0
    while True:
        code = bot.SendMessage(Type, target, soup.Forward(*node))
        if error_number == 5:
            bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),quote=Source.id)
        error_number += 1
        if type(code) is int:return
        if code == '30':
            top = []
            for n in node:
                if len(top) < len(n.messageChain):top = n.messageChain
            top[4] = soup.Plain(f'剩余 {top[4:]} 张被折叠，请使用 pid 查询')
            node[node.index(top)] = top[:5]