# -*- coding: utf-8 -*-

import json, os, time, random, re, traceback
from io import BytesIO
from pixivpy3 import AppPixivAPI
from pixivpy3.utils import PixivError
from PIL import Image, UnidentifiedImageError

import soup
from mainloop import AddWorkerTo, RemoveWorkerTo, Put, PutTo
from qr import img2qr
from admin import admin_ID
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from qqbotcls import QQBotSched, bot
from common import b64encode

password:str = '1064393873' # 不限时密钥
starttime = 1672531200 # 起始时间
life:int = 10800 # 链接时效 3*60*60
# 1672531200 - 10800 = 1672520400

fileserver = 'http://mdie.asuscomm.com:8888'

# 图片代理
hosts = [
    # 'i.pixiv.cat',
    'i.pixiv.re',
    'i.pixiv.nl',
]
def host():
    hosts.insert(0,hosts.pop())
    return hosts[0]

# pixiv配置
config = {
    'REFRESH_TOKEN':'',
    'USERNAME':'',
    'PASSWORD':''
}

tempdir = 'temp/pixiv'
if not os.path.exists(tempdir):os.makedirs(tempdir)

class Pixiv(AppPixivAPI):
    def __init__(self, **requests_kwargs): #初始化api
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
                if r.text:jsondict = self.parse_json(r.text)
                else:continue
                if hasattr(jsondict.error, 'message') and jsondict.error.message:
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
            except:
                traceback.print_exc()

pixiv = Pixiv()
requests = pixiv.requests

def get_tags(number=40):
    return "\n".join([f"{tag.tag}:{tag.translated_name}" for tag in pixiv.trending_tags_illust().trend_tags][:number])

def content(url: str) -> bool:
    with pixiv.requests_call("GET", url, headers={"Referer": "https://app-api.pixiv.net/"}, stream=True) as response:content = response.content
    return content

def ugoira_download(illust):
    delay = [frame.delay for frame in pixiv.ugoira_metadata(illust.id).ugoira_metadata.frames]
    def _temp(n,page_list):
        while True:
            url = illust.meta_single_page.original_image_url.replace('ugoira0.', f'ugoira{n}.').replace('i.pximg.net', host())
            try:page_list.append([n, Image.open(BytesIO(content(url)))])
            except UnidentifiedImageError:continue
            except Exception as e:WARNING(e)
            else:return
    AddWorkerTo('pixiv', 100)
    while True:
        try:
            page_list = []
            for n in range(len(delay)):
                PutTo('pixiv', _temp, n, page_list)
            while len(delay) != len(page_list):pass
            page_list.sort(key=lambda i:i[0])
            page_list[0][1].save(f'{tempdir}/{illust.id}.gif', save_all=True, append_images=[i[1] for i in page_list][1:], duration=delay, loop=0)
        except:pass
        break
    RemoveWorkerTo('pixiv', 100)
    
def illust_r18(illust, Group=True): # 在此容错
    if any(tag.name.lower() in ('r-18', 'r18', 'r-15', 'r15') for tag in illust.tags) and Group:
        soupimage = lambda word, url:img2qr(bot.Upload(content(word.replace('i.pximg.net', host()))).url, url.replace('i.pximg.net', host()))
        def soupimage(word, url):
            try:byte = content(word.replace('i.pximg.net', host()))
            except:byte = content(word)
            error_number = 0
            while True:
                image = bot.Upload(byte)
                if isinstance(image, tuple):
                    error_number += 1
                    continue
                try:return img2qr(image.url, url.replace('i.pximg.net', host()))
                except:return img2qr(image.url, url, headers={"Referer": "https://app-api.pixiv.net/"})
    else:
        soupimage = lambda word, url:soup.Image(word.replace('i.pximg.net', host()))
    return soupimage

def illust_msg(illust, Group=True, limit=80):
    Plain = f'标题:{illust.title} Pid:{illust.id}\n作者:{illust.user.name} Uid:{illust.user.id} {"T"if illust.user.is_followed else "F"}\n时间:{illust.create_date[:-6]}\n类型:{illust.type} 收藏:{illust.total_bookmarks} 标签:\n'
    for tag in illust.tags:Plain += f'{tag.name}:{tag.translated_name}\n'
    message = [soup.Plain(Plain + f'总共{illust.page_count}张\n临时链接时效三小时')]
    soupimage = illust_r18(illust, Group)
    if illust.type == 'ugoira':
        if not os.path.exists(f'{tempdir}/{illust.id}.gif'):ugoira_download(illust)
        url = f"{fileserver}/{b64encode('%d'%(time.time()-starttime+life)+f'{tempdir}/{illust.id}.gif')}"
        try:message += [img2qr(url, f'{tempdir}/{illust.id}.gif')]
        except:
            ERROR(traceback.format_exc())
            try:message += [img2qr(url, illust.image_urls.medium.replace('i.pximg.net', host()))]
            except:
                ERROR(traceback.format_exc())
                message += [img2qr(url, illust.image_urls.medium, headers={"Referer": "https://app-api.pixiv.net/"})]
    else:
        if illust.page_count > 1:
            imgs = [[page.image_urls.original, page.image_urls.medium] for page in illust.meta_pages[:limit]]
        else:
            imgs = [[illust.meta_single_page.original_image_url, illust.image_urls.medium]]
        url = re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+', imgs[0][0]).group()
        try:message += [img2qr(fileserver +'/'+ b64encode('%d/%s_%d%s' % (time.time()-starttime+life, url, illust.page_count, imgs[0][0][-3:])), imgs[0][1])]
        except:message += [img2qr(fileserver +'/'+ b64encode('%d/%s_%d%s' % (time.time()-starttime+life, url, illust.page_count, imgs[0][0][-3:])), imgs[0][1], headers={"Referer": "https://app-api.pixiv.net/"})]
        message += [soupimage(img[0], img[1]) for img in imgs]
    return message

def illust_node(illust, Type, target, sender=2854196310, name='QQ管家', Source=None): # 单插画消息链
    message = illust_msg(illust, Type=='Group')
    node = [soup.Node(sender, name, msg) for msg in message]
    for n in range(0, len(node), 50):
        error_number = 0
        while node:
            code, msgid = bot.SendMessage(Type, target, soup.Forward(*node[n:n+50], summary=f'总共{illust.page_count}张', preview=[f'{name}:{s}' for s in message[0].text.splitlines()][:4]))
            if not code and msgid > 0:break # -1被吞、20禁言、30超长、400客户端错误、500服务端错误（超大、超量、下载失败）
            elif code == 20:break
            elif code == 500:pass
            if msgid == -1 or code == 30 or error_number == 1:
                node = [soup.Node(sender, name, msg) for msg in message[:2]]
            if error_number == 1:
                bot.SendMessage(Type, target, soup.Plain(f'⚠️Pid:{illust.id} 图床超时请等待⚠️'), id=Source)
            if error_number == 2:
                bot.SendMessage(Type, target, soup.Plain(f'🆘Pid:{illust.id} 发送失败🆘'), id=Source)
                break
            error_number += 1

def illusts_node(illusts, Group=True): # 多插画消息链
    return [illust_msg(illust, Group ,3) for illust in illusts]

def send_illusts(Type, target, Source, node, msg=''):
    error_number = 0
    while node:
        code, msgid = bot.SendMessage(Type, target, soup.Forward(*node))
        if not code and msgid > 0:break
        elif code == 20:break
        elif code == 500:pass
        if msgid == -1 or code == 30 or error_number == 1:
            for n in node:
                n.messageChain = [n.messageChain[0], n.messageChain[1]]
        if error_number == 1:
            bot.SendMessage(Type, target, soup.Plain('⚠️图床超时请等待⚠️'), id=Source)
        if error_number == 2:
            bot.SendMessage(Type, target, soup.Plain(f'🆘{msg}发送失败🆘'), id=Source)
            break
        error_number += 1

def onPlug(bot):
    bot.pixiv = pixiv 
    try:
        if os.path.exists(bot.conf.Config('pixiv.json')):
            with open(bot.conf.Config('pixiv.json'), 'r', encoding='utf-8') as f:conf = json.load(f)
            for k, v in conf.items():
                if k in config and v:config[k] = v
        else:raise
    except:
        with open(bot.conf.Config('pixiv.json'), 'w', encoding='utf-8') as f:json.dump(config, f, ensure_ascii=False, indent=4)

    try:
        if config['REFRESH_TOKEN']:
            pixiv.set_auth(None, config['REFRESH_TOKEN'])
            pixiv.auth()
        elif config['USERNAME'] and config['PASSWORD']:
            pixiv.login(config['USERNAME'], config['PASSWORD'])
    except:
        WARNING('Pixiv 登陆失败，需要重启')
        Put(bot.Restart)

    if not hasattr(pixiv, 'PID'):
        try:
            if os.path.exists(bot.conf.Config('PID.json')):
                with open(bot.conf.Config('PID.json'), 'r', encoding='utf-8') as f:pixiv.PID = json.load(f)
            else:raise
        except:
            pixiv.PID = []
            with open(bot.conf.Config('PID.json'),'w', encoding='utf-8') as f:json.dump(pixiv.PID, f)

def onUnplug(bot):
    del bot.pixiv

def onInterval(bot): # 刷新令牌和保存PID记录
    while True:
        try:
            pixiv.auth(refresh_token=pixiv.refresh_token or config['REFRESH_TOKEN'])
            break
        except PixivError as e:
            ERROR(traceback.format_exc())
    with open(bot.conf.Config('PID.json'), 'w', encoding='utf-8') as f:json.dump(pixiv.PID, f)

@QQBotSched(month=1) # 减少PID记录
def week_clear_pid(bot):
    pixiv.PID = pixiv.PID[-1000:]

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
        targets:list|int=None,
        Type:str='Group', # 'Group'|'Friend'
        date:str=None # 'YYYY-mm-dd'
    ):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    next_url = {'mode':'day', 'date':date}
    illusts = []
    while next_url:
        illust_ranking = pixiv.illust_ranking(**next_url)
        next_url = pixiv.parse_qs(illust_ranking.next_url)
        for illust in illust_ranking.illusts:
            if illust.id not in pixiv.PID and len(illusts) < 10:
                illusts.append(illust)
                pixiv.PID.append(illust.id)
        if len(illusts) == 10:
            break
    if targets and type(targets) is not list:targets = [targets]
    else:targets = [g.id for g in bot.Group]
    if not targets:return
    node = [soup.Node(2854196310, 'QQ管家', soup.Plain(f'Pixiv {date or time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} 日榜单'))]
    node += [soup.Node(2854196310, 'QQ管家', *m) for m in illusts_node(illusts, 'Group'==Type)]
    for target in targets:
        send_illusts(Type, target, None, node, f'Pixiv {date or time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} 日榜单')
        time.sleep(30)
            
# Pixiv R-18日榜
@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=23, 
            minute=30, 
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def day_r18_ranking(
        bot,
        targets:list|int=None,
        Type:str='Group', # 'Group'|'Friend'
        date:str=None # 'YYYY-mm-dd'
    ):
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    next_url = {'mode':'day_r18', 'date':date}
    illusts = []
    while next_url:
        illust_ranking = pixiv.illust_ranking(**next_url)
        next_url = pixiv.parse_qs(illust_ranking.next_url)
        for illust in illust_ranking.illusts:
            if illust.id not in pixiv.PID and len(illusts) < 10:
                illusts.append(illust)
                pixiv.PID.append(illust.id)
        if len(illusts) == 10:
            break
    if targets and type(targets) is not list:targets = [targets]
    else:targets = [g.id for g in bot.Group]
    if not targets:return
    node = [soup.Node(2854196310, 'QQ管家', soup.Plain(f'Pixiv {date or time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} R18榜单'))]
    node += [soup.Node(2854196310, 'QQ管家', *m) for m in illusts_node(illusts, 'Group'==Type)]
    for target in targets:
        send_illusts(Type, target, None, node, f'Pixiv {date or time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} R18榜单')
        time.sleep(30)
    node = node[:1] + [soup.Node(2854196310, 'QQ管家', *m) for m in illusts_node(illusts, False)]
    for f in admin_ID():
        send_illusts('Friend', f, None, node, f'Pixiv {date or time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} R18榜单')
        time.sleep(30)

# Pixiv每日动态
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
def illust_follow(bot, date=None, send=True):
    if date is None:date = time.strftime("%Y-%m-%d", time.localtime())
    next_url = {'restrict':'all'}
    illust_new = []
    while next_url:
        illusts = pixiv.illust_follow(**next_url)
        for illust in illusts.illusts:
            if illust.create_date[:10] == date:
                illust_new.append(illust)
            elif illust.create_date[:10] > date:
                continue
            else:
                next_url = None
                break
        if next_url:
            next_url = pixiv.parse_qs(illusts.next_url)
    AddWorkerTo('pixiv', 10)
    for f in admin_ID():
        bot.SendMessage('Friend', f, soup.Plain(f'关注动态更新共 {len(illust_new)} 个'))
        bot.SendMessage('Friend', f, soup.Plain(b64encode('%d/%s' % (time.time()-1672520400, '/'.join([f'{i.id}-{i.page_count}{i.meta_single_page.original_image_url[-3:] if i.page_count == 1 else i.meta_pages[0].image_urls.original[-3:]}' for i in illust_new])))))
        if send:
            for illust in illust_new:
                PutTo('pixiv', illust_node, illust, 'Friend', f)
                time.sleep(10)
    RemoveWorkerTo('pixiv', 10)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 'setu'，'色图'或'涩图'，'瑟图'
    可附带 关键字 使用空格分隔
    最后指定数量（最多发10幅）
    返回pixiv插画推荐
    'Pid' 或 'Uid' 查询插画和作者
    '推荐关键字' 获取 趋势标签
    !!!群消息有概率被吞!!!'''
    if not hasattr(bot, 'pixiv'):onPlug(bot)
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    Group = hasattr(Sender, 'group')
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
    keyward = ('setu', '色图', '涩图', '瑟图', '来点色图', '来点瑟图', '来点涩图')

    if Plain == '推荐关键字' or Plain == '关键字推荐':
        bot.SendMessage(Type, target, soup.Plain(get_tags()))
        return

    elif Plain.lower().startswith('pid') or 'https://www.pixiv.net/member_illust.php?' in Plain or 'https://www.pixiv.net/artworks/' in Plain: # 通过PID获取插图
        if Plain.lower().startswith('pid'):
            try:pid = re.search(r'\d+', Plain)[0]
            except:
                bot.SendMessage(Type, target, soup.Plain('⚠️例:PID12345678'), id=Source.id)
                return
        elif 'https://www.pixiv.net/member_illust.php?' in Plain:
            try:pid = re.search(r'illust_id=\d+', Plain)[0].replace('illust_id=', '')
            except:return
        elif 'https://www.pixiv.net/artworks/' in Plain:
            try:pid = re.search(r'https://www.pixiv.net/artworks/\d+', Plain)[0].replace('https://www.pixiv.net/artworks/', '')
            except:return
        bot.SendMessage(Type, target, soup.Plain(f'PixivID:{pid} 获取中♾️'), id=Source.id)
        illust = pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'⚠️{k}:{v}'+'\n'), id=Source.id) for k, v in illust.error.items() if v]
            return
        if not (illust.illust.title or illust.illust.user.name):
            bot.SendMessage(Type, target, soup.Plain(f'⚠️{Plain}已删除或非公开'), id=Source.id)
            return
        illusts = [illust.illust]

    elif Plain.lower().startswith('uid') or 'https://www.pixiv.net/member.php?' in Plain or 'https://www.pixiv.net/users/' in Plain: # 通过UID获取用户作品
        if Plain.lower().startswith('uid'):
            try:uid = re.search(r'\d+', Plain)[0]
            except:
                bot.SendMessage(Type, target, soup.Plain('⚠️例:UID12345678'), id=Source.id)
                return
        elif 'https://www.pixiv.net/member.php?' in Plain:
            try:uid = re.search(r'id=\d+', Plain)[0].replace('id=', '')
            except:return
        elif 'https://www.pixiv.net/users/' in Plain:
            try:uid = re.search(r'https://www.pixiv.net/users/\d+', Plain)[0].replace('https://www.pixiv.net/users/', '')
            except:return
        bot.SendMessage(Type, target, soup.Plain(f'UserID:{uid} 获取中♾️'), id=Source.id)
        user = pixiv.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'⚠️{k}:{v}'+'\n')) for k, v in user.error.items() if v]
            return
        if 'i.pximg.net' in user.user.profile_image_urls.medium:message = soup.Image(user.user.profile_image_urls.medium.replace('i.pximg.net', host())),
        else:message = soup.Image(base64=content(user.user.profile_image_urls.medium)),
        message += soup.Plain(f"\nUid:{user.user.id}\n名字:{user.user.name}\n插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *message))
        admin_node.append(soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *message))
        illusts = pixiv.user_illusts(user.user.id).illusts[:10] + pixiv.user_illusts(user.user.id, 'manga').illusts[:10]
        illusts.sort(key=lambda i:i.create_date, reverse=True)
        illusts = illusts[:10]

    elif Plain.lower().startswith(keyward) or (bot.conf.qq in At and any(kw for kw in keyward if kw in Plain.lower())): # 随机色图和搜索
        for kw in keyward:Plain = Plain.replace(kw, '').strip()
        number = re.findall(r' \d+', Plain)
        if number and Plain.endswith(number[-1]):
            Plain = Plain.replace(number[-1], '').strip()
            number = int(number[-1])
        else:
            number = 1
        bot.SendMessage(Type, target, soup.Plain(f'关键字：{Plain} 获取中♾️'), id=Source.id)
        illusts = []
        bookmarks = [100000, 90000, 80000, 70000, 60000, 50000, 40000, 30000, 20000,10000, 5000, 1000, 500, 250, 100, 0]
        for bookmark in bookmarks:
            next_url = {'word':f'{Plain}{f" {bookmark}users入り"if bookmark else ""}'}
            loopnum = 0
            while next_url:
                p = pixiv.search_illust(**next_url)
                next_url = pixiv.parse_qs(p.next_url)
                if next_url:p.illusts.sort(key=lambda i:i.total_bookmarks, reverse=True)
                else:break
                for i in p.illusts:
                    if (i.total_bookmarks >= bookmark/2 >=50 or (250 >= bookmark and i.total_bookmarks >= 50)) and \
                        ((i.type == 'manga' and random.randint(0, 1)) or i.type != 'manga') and \
                        i.id not in pixiv.PID and \
                        i.page_count<=50:
                        illusts.append(i)
                        pixiv.PID.append(i.id)
                    else:print(bookmark, i.total_bookmarks, i.id)
                    if len(illusts) == number or len(illusts) == 10:break
                if len(illusts) == number or len(illusts) == 10 or loopnum >= 50:break
                loopnum += 1
            if len(illusts) == number or len(illusts) == 10:break
        if not illusts:
            bot.SendMessage(Type, target, soup.Plain(f'没有"{Plain}"的相关结果，请考虑空格分割关键字或使用日语关键字:\n'+get_tags(20)), id=Source.id)
            return
    else:return

    if len(illusts) == 1:
        illust_node(illusts[0], Type, target, Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, Source.id)
        if Sender.id in admin_ID():return
        for f in admin_ID():
            illust_node(illusts[0], 'Friend', f, Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, Source.id)
        return
        
    node += [soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *m) for m in illusts_node(illusts, Group)]
    send_illusts(Type, target, Source.id, node)
    if Sender.id in admin_ID():return
    if Group:admin_node += [soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *m) for m in illusts_node(illusts, False)]
    else:admin_node = node
    for f in admin_ID():
        send_illusts('Friend', f, None, admin_node)