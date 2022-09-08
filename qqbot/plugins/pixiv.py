# -*- coding: utf-8 -*-

import json, os, time, traceback, requests
from admin import admin_ID

import soup
from utf8logger import WARNING
from pixivpy3 import ByPassSniApi
from qqbotcls import QQBotSched

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

def illust_node(illust,bot,Type,target,sender=2854196310, name='QQ管家',Source=None):
    Plain = f'标题:{illust.title} Pid:{illust.id}\n作者:{illust.user.name} Uid:{illust.user.id}\n时间:{illust.create_date}\n类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:'
    for tag in illust.tags:Plain += f'\n{tag.name}:{tag.translated_name}'
    node = soup.Node(sender,name,soup.Plain(Plain)),
    if 'R-18' in Plain and Type=='Group':
        if illust.page_count > 1:
            for page in illust.meta_pages:
                node += soup.Plain('\n'+page.image_urls.original.replace('i.pximg.net',hosts)),
        else:
            node += soup.Plain('\n'+illust.meta_single_page.original_image_url.replace('i.pximg.net',hosts)),
    elif illust.page_count > 1:
        for page in illust.meta_pages:
            node += soup.Node(sender,name,soup.Image(url=page.image_urls.original.replace('i.pximg.net',hosts))),
    else:
        node += soup.Node(sender,name,soup.Image(url=illust.meta_single_page.original_image_url.replace('i.pximg.net',hosts))),
    error_number = 0
    for n in range(0,len(node),50):
        while True:
            code = bot.SendMessage(Type, target, soup.Forward(*node[n:n+50]))
            if error_number == 5:
                bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),id=Source)
            error_number += 1
            if type(code) is int:break

def illusts_node(illusts, sender=2854196310, name='QQ管家', Group=True):
    node = []
    for i in illusts:
        if i.type == 'ugoira':continue
        Plain = f'标题:{i.title} Pid:{i.id}\n作者:{i.user.name} Uid:{i.user.id}\n时间:{i.create_date}\n类型:{i.type} 收藏:{i.total_bookmarks} 标签:\n'
        for tag in i.tags:Plain += f'{tag.name}:{tag.translated_name}\n'
        message = [soup.Plain(Plain)]
        if 'R-18' in Plain and Group:
            if i.page_count > 1:
                for page in i.meta_pages:
                    message.append(soup.Plain('\n'+page.image_urls.original.replace('i.pximg.net',hosts)))
            else:
                message.append(soup.Plain('\n'+i.meta_single_page.original_image_url.replace('i.pximg.net',hosts)))
        elif i.page_count > 1:
            for page in i.meta_pages:
                message.append(soup.Image(url=page.image_urls.original.replace('i.pximg.net',hosts)))
        else:
            message.append(soup.Image(url=i.meta_single_page.original_image_url.replace('i.pximg.net',hosts)))
        node.append(soup.Node(sender,name,*message))
    return node

def fold_node(node):
    top = node[0]
    for n in node:
        if len(top.messageChain) < len(n.messageChain):top = n
    msg = f'\n{top.messageChain[4].url}\n~~~'
    msg += f'\n{top.messageChain[-1].url}\n'
    msg += f'剩余 {len(top.messageChain[4:])} 张被折叠，请使用 pid 查询'
    top.messageChain = top.messageChain[:4]
    top.messageChain.append(soup.Plain(msg))
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
        bot.pixiv = Pixiv("public-api.secure.pixiv.net")
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
def week_r18(bot):
    bot.r18['viewed'] = []

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=8, 
            minute=None, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_ranking(bot,target=None,Type='Group'):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking(mode='day')
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} 日榜单'))]
    node += illusts_node(illusts.illusts[:10], Group='Group'==Type)
    if target:
        while True:
            code = bot.SendMessage(Type,target, soup.Forward(*node))
            if type(code) is int:return
            if code == '30':node = fold_node(node)
    for g in bot.Group:
        while True:
            code = bot.SendMessage('Group',g.id, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = fold_node(node)
            

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
def day_r18_ranking(bot,target=None,Type='Group'):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day_r18')
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv R18榜单'))]
    node += illusts_node(illusts.illusts[:10], Group=bool(target))
    if target:
        while True:
            code = bot.SendMessage(Type,target, soup.Forward(*node))
            if type(code) is int:return
            if code == '30':node = fold_node(node)
    for f in admin_ID():
        while True:
            code = bot.SendMessage('Friend',f, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = fold_node(node)

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=23, 
            minute=59, 
            second=59, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def illust_follow(bot):
    next_url = {'restrict':'all'}
    illust_new = []
    while next_url:
        illusts = bot.pixiv.illust_follow(**next_url)
        for illust in illusts.illusts:
            if illust.create_date >= time.strftime("%Y-%m-%d",time.localtime(time.time()-86400)):
                illust_new.append(illust)
            else:
                next_url = None
                break
        if next_url:
            next_url = bot.pixiv.parse_qs(illusts.next_url)
    for f in admin_ID():
        for illust in illust_new:
            illust_node(illust,bot,'Friend',f)
    
def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 'setu','色图'或'涩图'(可指定数量)
    返回pixiv插画推荐（最多发15幅图）
    Pid Uid 查询
    -=#群消息有概率被吞#=-'''
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    if Type not in ['Friend', 'Group']:return
    Group = hasattr(Sender, 'group')
    if Group:target = Sender.group.id
    else:target = Sender.id
    Plain = ''
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
    Plain = Plain.lower()

    node = []
    keyward = ('setu','色图','涩图')
    Plain = Plain.replace(' ','').replace(':','').replace('：','')
    if Plain.startswith('pid'):
        try:pid = int(Plain[3:])
        except:
            bot.SendMessage(Type,target,soup.Plain('例:PID12345678'))
            return
        illust = bot.pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in illust.error.items() if v]
            return
        illust_node(illust.illust,bot,Type,target,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        for f in bot.Friend:
            if f.remark != 'Admin' or f.nickname == 'Admin':continue
            illust_node(illust.illust,bot,'Friend',f.id,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        return

    elif Plain.startswith('uid'):
        try:uid = int(Plain[3:])
        except:
            bot.SendMessage(Type,target,soup.Plain('例:UID12345678'))
            return
        user = bot.pixiv.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in user.error.items() if v]
            return
        message = soup.Image(user.user.profile_image_urls.medium.replace('i.pximg.net',hosts)),
        message += soup.Plain(f"Uid:{user.user.id} 名字:{user.user.name}\n 插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*message))
        illusts = bot.pixiv.user_illusts(user.user.id).illusts[:10]

    elif Plain.startswith(keyward):
        for kw in keyward:Plain = Plain.replace(kw,'')
        if Plain.startswith(('r18', 'r-18')): # r18
            for illust in bot.pixiv.illust_ranking('day_r18',offset=bot.r18['offset']).illusts:
                bot.r18['offset'] += 1
                if illust.id not in bot.r18['viewed']:
                    bot.r18['viewed'].append(illust.id)
                    break
            else:
                while True:
                    illust = bot.pixiv.illust_detail(requests.get('https://api.lolicon.app/setu/v2?r18=1').json()['data'][0]['pid'])
                    if 'error' not in illust:
                        illust = illust.illust
                        break
            illusts = [illust]
        else: # 正常推荐
            try:number = int(Plain)
            except:number = 1
            else:number = (number > 15 and 15) or (number < 1 and 1) or number
            illusts = bot.pixiv.illust_recommended().illusts[:number]

    else:return

    node += illusts_node(illusts,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname, Group)
    error_number = 0
    while True:
        code = bot.SendMessage(Type, target, soup.Forward(*node))
        if error_number == 5:
            bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),id=Source.id)
        error_number += 1
        if type(code) is int:
            for f in bot.Friend:
                if f.remark != 'Admin' or f.nickname == 'Admin':continue
                bot.SendMessage('Friend', f.id, soup.Forward(*node))
            return
        if code == '30':
            fold_node(node)