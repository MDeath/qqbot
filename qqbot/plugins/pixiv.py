# -*- coding: utf-8 -*-

import json, os, time, random, re
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import PixivError

import soup
from mainloop import Put
from qr import imgurl2qr
from admin import admin_ID
from utf8logger import ERROR,INFO,WARNING
from qqbotcls import QQBotSched

# 图片代理
hosts = {
    'cat' : 'i.pixiv.cat',
    're' : 'i.pixiv.re',
    'nl' : 'i.pixiv.nl',
    'lolisuki' : 'pixiv.lolisuki.cn'
}
hosts = hosts['nl']
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

    def require_auth(self) -> None:
        if self.access_token is None:
            self.auth()

    def no_auth_requests_call(self, *args, **kwargs):
        while True:
            try:
                r = super().no_auth_requests_call(*args, **kwargs)
                if r.ok:return r
                jsondict = self.parse_json(r.text)
                if hasattr(jsondict.error,'message') and jsondict.error.message:
                    if 'Rate Limit' in jsondict.error.message:
                        time.sleep(10)
                        continue
                    elif 'Error occurred at the OAuth process.' in jsondict.error.message:
                        self.auth(refresh_token=self.refresh_token or config['REFRESH_TOKEN'])
                        continue
                return r
            except PixivError as e:
                if str(e).startswith('[ERROR] auth() failed! check refresh_token.'):self.auth()
                elif str(e).startswith('Authentication required! Call login() or set_auth() first!'):self.auth()
                else:raise PixivError(e)


    def get_tags(self,number=40):
        return "\n".join([f"{tag.tag}:{tag.translated_name}" for tag in self.trending_tags_illust().trend_tags][:number])
    
def illust_node(illust,bot,Type,target,sender=2854196310, name='QQ管家',Source=None): # 单插画消息链
    Plain = f'标题:{illust.title} Pid:{illust.id}\n作者:{illust.user.name} Uid:{illust.user.id}\n时间:{illust.create_date}\n类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:'
    for tag in illust.tags:Plain += f'\n{tag.name}:{tag.translated_name}'
    node = soup.Node(sender,name,soup.Plain(Plain)),

    if any(kw in Plain.lower() for kw in ('r-18', 'r18', 'r-15', 'r15')) and Type == 'Group':
        souptype = lambda word,url:soup.Node(sender,name,imgurl2qr(word.replace('i.pximg.net',hosts),url.replace('i.pximg.net',hosts)))
    else:
        souptype = lambda word,url:soup.Node(sender,name,soup.Image(word.replace('i.pximg.net',hosts)))

    if illust.page_count > 1:
        for page in illust.meta_pages:
            node += souptype(page.image_urls.original,page.image_urls.medium),
    else:
        node += souptype(illust.meta_single_page.original_image_url,illust.image_urls.medium),
    error_number = 0

    for n in range(0,len(node),50):
        while node:
            code = bot.SendMessage(Type, target, soup.Forward(*node[n:n+50]))
            if error_number == 5:
                bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),id=Source)
            error_number += 1
            if code == -1:img2qr(node)
            elif type(code) is int:break
            elif code == '500':break

def illusts_node(illusts, sender=2854196310, name='QQ管家', Group=True): # 多插画消息链
    node = []
    
    for i in illusts:
        if i.type == 'ugoira':continue
        Plain = f'标题:{i.title} Pid:{i.id}\n作者:{i.user.name} Uid:{i.user.id}\n时间:{i.create_date}\n类型:{i.type} 收藏:{i.total_bookmarks} 标签:\n'
        for tag in i.tags:Plain += f'{tag.name}:{tag.translated_name}\n'
        message = [soup.Plain(Plain)]

        if any(kw in Plain.lower() for kw in ('r-18', 'r18', 'r-15', 'r15')) and Group:
            souptype = lambda word,url:imgurl2qr(word.replace('i.pximg.net',hosts),url.replace('i.pximg.net',hosts))
        else:
            souptype = lambda word,url:soup.Image(word.replace('i.pximg.net',hosts))

        if i.page_count > 1:
            for page in i.meta_pages:
                message.append(souptype(page.image_urls.original,page.image_urls.medium))
        else:
            message.append(souptype(i.meta_single_page.original_image_url,i.image_urls.medium))

        node.append(soup.Node(sender,name,*message))
    return node

def fold_node(node): # 折叠图片最多的消息
    top = node[0]
    for n in node:
        if len(top.messageChain) < len(n.messageChain):top = n
    msg = f'\n剩余 {len(top.messageChain[4:])} 张被折叠，请使用 pid 查看详情'
    top.messageChain = top.messageChain[:4]
    top.messageChain.append(soup.Plain(msg))

def img2qr(node:soup.Node): # messageId=-1，全部图片转QRCode
    for n in node:
        if len(n.messageChain) == 2 and n.messageChain[0].type == 'Image' and n.messageChain[1].type == 'Plain':continue
        for m in range(len(n.messageChain)):
            if n.messageChain[m].type == 'Image':n.messageChain[m] = imgurl2qr(picture=n.messageChain[m].url)

def onPlug(bot):
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
    except:
        WARNING('Pixiv 登陆失败,需要重启')
        Put(bot.Restart)

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

def onInterval(bot): # 刷新令牌和保存PID记录
    while True:
        try:
            bot.pixiv.auth(refresh_token=bot.pixiv.refresh_token or config['REFRESH_TOKEN'])
            break
        except PixivError as e:
            ERROR(e)
    with open(bot.conf.Config('PID.json'),'w', encoding='utf-8') as f:json.dump(bot.pixiv.PID,f)

@QQBotSched(month=1) # 清空PID记录
def week_clear_pid(bot):
    bot.pixiv.PID = []

# Pixiv日榜
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
def day_ranking(
        bot,
        target:list|int=None,
        Type:str='Group', # 'Group'|'Friend'
        date:str=None # 'YYYY-mm-dd'
    ):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day',date=date)
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {date or time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} 日榜单'))]
    node += illusts_node(illusts.illusts[:10], Group='Group'==Type)
    if target and type(target) is not list:target = [target]
    else:target = [g.id for g in bot.Group]
    for tg in target:
        while node:
            code = bot.SendMessage(Type, tg, soup.Forward(*node))
            if code == -1:img2qr(node)
            elif type(code) is int:break
            elif code == '30':fold_node(node)
        time.sleep(30)
            
# Pixiv R-18日榜
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
def day_r18_ranking(
        bot,
        target:list|int=None,
        Type:str='Group', # 'Group'|'Friend'
        date:str=None # 'YYYY-mm-dd'
    ):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    illusts = bot.pixiv.illust_ranking('day_r18',date=date)
    node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {date or time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} R18榜单'))]
    node += illusts_node(illusts.illusts[:10], Group=Type=="Group")
    if target and type(target) is not list:target = [target]
    else:target = [g.id for g in bot.Group]
    for tg in target:
        while node:
            code = bot.SendMessage(Type, tg, soup.Forward(*node))
            if code == -1:img2qr(node)
            elif type(code) is int:break
            elif code == '30':fold_node(node)
    admin_node = [soup.Node(2854196310,'QQ管家',soup.Plain(f'Pixiv {date or time.strftime("%Y-%m-%d",time.localtime(time.time()-86400))} R18榜单'))]
    admin_node += illusts_node(illusts.illusts[:10], Group=False)
    for f in admin_ID():
        if f in target:continue
        while admin_node:
            code = bot.SendMessage('Friend',f, soup.Forward(*admin_node))
            if type(code) is int:break
            elif code == '30':fold_node(admin_node)
        time.sleep(30)

# Pixiv每日动态
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
    '推荐关键字' 获取 趋势标签
    !!!群消息有概率被吞!!!'''
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    Group = hasattr(Sender,'group')
    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = Sender.id, Sender.group.id

    Plain = ''
    At = []
    for msg in Message:
        if msg.type == 'At':At.append(msg.target)
        if msg.type == 'Plain':Plain += msg.text

    node = []
    admin_node = []
    keyward = ('setu','色图','涩图','瑟图')

    if Plain == '推荐关键字' or Plain == '关键字推荐':
        bot.SendMessage(Type, target, soup.Plain(bot.pixiv.get_tags()))
        return

    elif Plain.lower().startswith('pid'): # 通过PID获取插图
        try:pid = re.search(r'\d+',Plain)[0]
        except:
            bot.SendMessage(Type, target, soup.Plain('例:PID12345678'), id=Source.id)
            return
        bot.SendMessage(Type, target, soup.Plain('PixivID获取中'), id=Source.id)
        illust = bot.pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'{k}:{v}'+'\n'), id=Source.id) for k,v in illust.error.items() if v]
            return
        if not (illust.illust.title or illust.illust.user.name):
            bot.SendMessage(Type, target, soup.Plain(f'{Plain}已删除或非公开'), id=Source.id)
            return
        illust_node(illust.illust,bot,Type,target,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        for f in admin_ID():
            if Sender.id == f:continue
            illust_node(illust.illust,bot,'Friend',f,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,Source.id)
        return

    elif Plain.lower().startswith('uid'): # 通过UID获取用户作品
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
        message += soup.Plain(f"\nUid:{user.user.id}\n名字:{user.user.name}\n插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*message))
        admin_node.append(soup.Node(Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname,*message))
        illusts = bot.pixiv.user_illusts(user.user.id).illusts[:10]

    elif Plain.lower().startswith(keyward) or Plain.lower().endswith(keyward) or (bot.conf.qq in At and any(kw for kw in keyward if kw in Plain.lower())): # 随机色图和搜索
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
        bookmarks = [100000,90000,80000,70000,60000,50000,40000,30000,20000,10000,5000,1000,500,250,100,0]
        for bookmark in bookmarks:
            next_url = {'word':f'{Plain}{(bookmark and f" {bookmark}users入り") or ""}'}
            loopnum = 0
            while next_url:
                p = bot.pixiv.search_illust(**next_url)
                next_url = bot.pixiv.parse_qs(p.next_url)
                for i in p.illusts:
                    if (i.total_bookmarks >= bookmark >=50 or 250 >= bookmark >= i.total_bookmarks >= 50) and \
                        ((i.type == 'manga' and random.randint(0,1)) or i.type != 'manga') and \
                        i.id not in bot.pixiv.PID and \
                        i.page_count<=50:
                        for tag in i.tags:
                            if tag.name.lower() in ('r-18', 'r18', 'r-15', 'r15') and not Rtag:
                                break
                        else:
                            illusts.append(i)
                            bot.pixiv.PID.append(i.id)
                    if len(illusts) == number or len(illusts) == 10:break
                if len(illusts) == number or len(illusts) == 10 or loopnum >= 50:break
                loopnum += 1
                time.sleep(5)
            if len(illusts) == number or len(illusts) == 10:break
            time.sleep(5)

    else:return

    if not illusts:
        bot.SendMessage(Type, target, soup.Plain(f'没有"{Plain}"的相关结果,请考虑使用空格分割关键字,或使用推荐关键字:\n'+bot.pixiv.get_tags(20)), id=Source.id)
        return
    node += illusts_node(illusts,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname, Group)
    error_number = 0
    while node:
        code = bot.SendMessage(Type, target, soup.Forward(*node))
        if error_number == 5:bot.SendMessage(Type, target, soup.Plain('图床超时请等待'),id=Source.id)
        error_number += 1
        if code == -1:img2qr(node)
        elif type(code) is int:break
            # for f in admin_ID():
            #     if Sender.id == f:continue
            #     bot.SendMessage('Friend', f, soup.Forward(*node))
            # return
        elif code == '30':fold_node(node)
    admin_node += illusts_node(illusts,Sender.id,(hasattr(Sender,'memberName') and Sender.memberName) or Sender.nickname, False)
    for f in admin_ID():
        while admin_node:
            if Sender.id == f:continue
            code = bot.SendMessage('Friend',f, soup.Forward(*admin_node))
            if type(code) is int:break
            elif code == '30':fold_node(admin_node)
            elif code == '500':break