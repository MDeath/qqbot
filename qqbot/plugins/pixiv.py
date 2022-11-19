# -*- coding: utf-8 -*-

import json, os, time, re
from pixivpy3 import AppPixivAPI

import soup
from qr import imgurltoqr
from admin import admin_ID
from utf8logger import WARNING
from qqbotcls import QQBotSched

# 图片代理
hosts = {
    'cat' : 'i.pixiv.cat',
    're' : 'i.pixiv.re',
    'lolisuki' : 'pixiv.lolisuki.cn'
}
hosts = hosts['lolisuki']
# pixiv配置
config = {
    'REFRESH_TOKEN':'',
    'USERNAME':'',
    'PASSWORD':''
}

class Pixiv(AppPixivAPI):
    def __init__(self,**requests_kwargs): #初始化api
        super().__init__(**requests_kwargs)
        self.set_accept_language('zh-cn')

    def no_auth_requests_call(self, *args, **kwargs):
        while True:
            r = super().no_auth_requests_call(*args, **kwargs)
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
                    self.auth(refresh_token=self.refresh_token or config['REFRESH_TOKEN'])
                    continue
            return r
    
    def auth(self, **kwavgs):
        kwavgs['refresh_token'] = self.refresh_token or config['REFRESH_TOKEN']
        return super().auth(**kwavgs)

def illust_node(illust,bot,Type,target,sender=2854196310, name='QQ管家',Source=None):
    Plain = f'标题:{illust.title} Pid:{illust.id}\n作者:{illust.user.name} Uid:{illust.user.id}\n时间:{illust.create_date}\n类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:'
    for tag in illust.tags:Plain += f'\n{tag.name}:{tag.translated_name}'
    node = soup.Node(sender,name,soup.Plain(Plain)),
    if any(kw in Plain.lower() for kw in ('r-18', 'r18', 'r-15', 'r15')) and Type == 'Group':
        souptype = lambda url:soup.Node(sender,name,imgurltoqr(url.replace('i.pximg.net',hosts)))
    else:
        souptype = lambda url:soup.Node(sender,name,soup.Image(url.replace('i.pximg.net',hosts)))
    if illust.page_count > 1:
        for page in illust.meta_pages:
            node += souptype(page.image_urls.original),
    else:
        node += souptype(illust.meta_single_page.original_image_url),
    error_number = 0
    for n in range(0,len(node),50):
        while node:
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
        if any(kw in Plain.lower() for kw in ('r-18', 'r18', 'r-15', 'r15')) and Group:
            souptype = lambda url:imgurltoqr(url.replace('i.pximg.net',hosts))
        else:
            souptype = lambda url:soup.Image(url.replace('i.pximg.net',hosts))
        if i.page_count > 1:
            for page in i.meta_pages:
                message.append(souptype(page.image_urls.original))
        else:
            message.append(souptype(i.meta_single_page.original_image_url))
        node.append(soup.Node(sender,name,*message))
    return node

def fold_node(node):
    top = node[0]
    for n in node:
        if len(top.messageChain) < len(n.messageChain):top = n
    msg = f'\n剩余 {len(top.messageChain[4:])} 张被折叠，请使用 pid 查看详情'
    top.messageChain = top.messageChain[:4]
    top.messageChain.append(soup.Plain(msg))
    return node

def onPlug(bot): # 群限制用和登录pixiv
    try:
        if os.path.exists(bot.conf.Config('pixiv.json')):
            with open(bot.conf.Config('pixiv.json'), 'r', encoding='utf-8') as f:conf = json.load(f)
            for k,v in conf.items():
                if k in config and v:config[k] = v
        else:raise
    except:
        with open(bot.conf.Config('pixiv.json'),'w', encoding='utf-8') as f:json.dump(config, f, ensure_ascii=False, indent=4)
    bot.pixiv = Pixiv()
    try:
        if config['REFRESH_TOKEN']:
            bot.pixiv.set_auth(None, config['REFRESH_TOKEN'])
            bot.pixiv.auth()
        elif config['USERNAME'] and config['PASSWORD']:
            bot.pixiv.login(config['USERNAME'],config['PASSWORD'])
    except:pass
    if not hasattr(bot.pixiv,'PID'):
        try:
            if os.path.exists(bot.conf.Config('PID.json')):
                with open(bot.conf.Config('PID.json'), 'r', encoding='utf-8') as f:bot.pixiv.PID = json.load(f)
            else:raise
        except:
            bot.pixiv.PID = []
            with open(bot.conf.Config('PID.json'),'w', encoding='utf-8') as f:json.dump(bot.pixiv.PID,f)

def onUnplug(bot):
    del bot.pixiv

def onInterval(bot): # 刷新群限制和刷新令牌
    bot.pixiv.auth(refresh_token=bot.pixiv.refresh_token or config['REFRESH_TOKEN'])
    with open(bot.conf.Config('PID.json'),'w', encoding='utf-8') as f:json.dump(bot.pixiv.PID,f)

@QQBotSched(day_of_week=1)
def week_clear_pid(bot):
    bot.pixiv.PID = []

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
def day_ranking(bot,target=None,Type='Group',date=None):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day',date=date)
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} 日榜单'))]
    node += illusts_node(illusts.illusts[:10], Group='Group'==Type)
    if target:
        while node:
            code = bot.SendMessage(Type,target, soup.Forward(*node))
            if type(code) is int:return
            if code == '30':node = fold_node(node)
    for g in bot.Group:
        while node:
            code = bot.SendMessage('Group',g.id, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = fold_node(node)
            

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=23, 
            minute=None, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_r18_ranking(bot,target=None,Type='Group',date=None):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day_r18',date=date)
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv R18榜单'))]
    node += illusts_node(illusts.illusts[:10], Group=Type=="Group")
    if target:
        while node:
            code = bot.SendMessage(Type,target, soup.Forward(*node))
            if type(code) is int:return
            if code == '30':node = fold_node(node)
    for g in bot.Group:
        while node:
            code = bot.SendMessage('Group',g.id, soup.Forward(*node))
            if type(code) is int:break
            if code == '30':node = fold_node(node)
    for f in admin_ID():
        if target == f:continue
        code = bot.SendMessage('Friend',f, soup.Forward(*node))

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
def illust_follow(bot):
    next_url = {'restrict':'all'}
    illust_new = []
    while next_url:
        illusts = bot.pixiv.illust_follow(**next_url)
        for illust in illusts.illusts:
            if illust.create_date[:10] > time.strftime("%Y-%m-%d",time.localtime(time.time()-86400)):
                continue
            if illust.create_date[:10] == time.strftime("%Y-%m-%d",time.localtime(time.time()-86400)):
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
    发送 'setu','色图'或'涩图','瑟图'
    可附带 关键字 使用空格分隔
    最后指定数量（最多发10幅）
    返回pixiv插画推荐
    'Pid' 或 'Uid' 查询插画和作者
    !!!群消息有概率被吞!!!'''
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    if Type not in ['Friend','Group']:return
    Group = hasattr(Sender, 'group')
    if Group:target = Sender.group.id
    else:target = Sender.id
    Plain = ''
    At = []
    for msg in Message:
        if msg.type == 'At':At.append(msg.target)
        if msg.type == 'Plain':Plain += msg.text

    node = []
    keyward = ('setu','色图','涩图','瑟图')
    if Plain.lower().startswith('pid'):
        try:pid = re.search(r'\d+',Plain)[0]
        except:
            bot.SendMessage(Type, target, soup.Plain('例:PID12345678'), id=Source.id)
            return
        bot.SendMessage(Type, target, soup.Plain('PixivID获取中'), id=Source.id)
        illust = bot.pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in illust.error.items() if v]
            return
        illust_node(illust.illust,bot,Type,target,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        for f in admin_ID():
            if Sender.id == f:continue
            illust_node(illust.illust,bot,'Friend',f,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        return

    elif Plain.lower().startswith('uid'):
        try:uid = re.search(r'\d+',Plain)[0]
        except:
            bot.SendMessage(Type, target, soup.Plain('例:UID12345678'), id=Source.id)
            return
        bot.SendMessage(Type, target, soup.Plain('UserID获取中'), id=Source.id)
        user = bot.pixiv.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n')) for k,v in user.error.items() if v]
            return
        message = soup.Image(user.user.profile_image_urls.medium.replace('i.pximg.net',hosts)),
        message += soup.Plain(f"Uid:{user.user.id} 名字:{user.user.name}\n 插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*message))
        illusts = bot.pixiv.user_illusts(user.user.id).illusts[:10]

    elif Plain.lower().startswith(keyward) or Plain.lower().endswith(keyward) or (bot.conf.qq in At and any(kw for kw in keyward if kw in Plain.lower())):
        bot.SendMessage(Type, target, soup.Plain('获取中'), id=Source.id)
        for kw in keyward:Plain = Plain.replace(kw,'').strip()
        Rtag = False
        for kw in ('r-18', 'r18', 'r-15', 'r15'):
            if kw in Plain.lower():
                Rtag = True
                break
        number = re.findall(r'\d+',Plain)
        if number and Plain.endswith(number[-1]) and not Plain.lower().endswith(('r-18', 'r18', 'r-15', 'r15')):
            Plain = Plain[:-len(number[-1])].strip()
            number = int(number[-1])
        else:
            number = 1
        illusts = []
        bookmarks = [100000,90000,80000,70000,60000,50000,40000,30000,20000,10000,5000,1000,500,250,100]
        for bookmark in bookmarks:
            next_url = {'word':f'{Plain} {bookmark}users入り'}
            while next_url:
                p = bot.pixiv.search_illust(**next_url)
                next_url = bot.pixiv.parse_qs(p.next_url)
                for i in p.illusts:
                    if (i.total_bookmarks >= bookmark or i.total_bookmarks >= 500) and i.id not in bot.pixiv.PID:
                        for tag in i.tags:
                            if tag.name.lower() in ('r-18', 'r18', 'r-15', 'r15') and not Rtag:
                                break
                        else:
                            illusts.append(i)
                            bot.pixiv.PID.append(i.id)
                    if len(illusts) == number or len(illusts) == 10:break
                if len(illusts) == number or len(illusts) == 10:break
            if len(illusts) == number or len(illusts) == 10:break

    else:return

    if not illusts:
        bot.SendMessage(Type, target, soup.Plain(f'没有 "{Plain}" 的相关结果'), id=Source.id)
        return
    node += illusts_node(illusts,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname, Group)
    error_number = 0
    while node:
        code = bot.SendMessage(Type, target, soup.Forward(*node))
        if error_number == 5:
            bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),id=Source.id)
        error_number += 1
        if type(code) is int:
            for f in admin_ID():
                if Sender.id == f:continue
                bot.SendMessage('Friend', f, soup.Forward(*node))
            return
        if code == '30':
            fold_node(node)