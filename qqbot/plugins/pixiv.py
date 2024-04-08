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
hosts = [ # 'https://i.pximg.net'
    # 'https://i.pixiv.cat',
    'https://i.pixiv.re',
    'https://i.pixiv.nl',
    # 'https://i-cf.pximg.net',
    # 'http://mdie.asuscomm.com:8888',
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
            url = illust.meta_single_page.original_image_url.replace('ugoira0.', f'ugoira{n}.')
            try:page_list.append([n, Image.open(BytesIO(content(url)))])
            except UnidentifiedImageError:continue
            except Exception as e:WARNING(e)
            else:return
    AddWorkerTo('pixiv', 10)
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
    RemoveWorkerTo('pixiv', 10)

def illust_msg(illust, Group=True, limit=100): # 插画生成消息连
    Plain = f'标题:{illust.title} Pid:{illust.id}\n作者:{illust.user.name} Uid:{illust.user.id} {"T"if illust.user.is_followed else "F"}\n时间:{illust.create_date[:-6]}\n类型:{illust.type} 收藏比:{illust.total_bookmarks}/{illust.total_view},{"%.2f"%(illust.total_bookmarks/illust.total_view*100)}% 标签:\n'
    for tag in illust.tags:Plain += f'{tag.name}:{tag.translated_name}\n'
    message = [soup.Plain(Plain + f'总共{illust.page_count}张,链接时效三小时')]
    if illust.type == 'ugoira':
        if not os.path.exists(f'{tempdir}/{illust.id}.gif'):ugoira_download(illust)
        url = f"{fileserver}/{b64encode('%d'%(time.time()-starttime+life)+f'{tempdir}/{illust.id}.gif')}"
        try:message += [img2qr(url, f'{tempdir}/{illust.id}.gif')]
        except:
            ERROR(traceback.format_exc())
            try:message += [img2qr(url, illust.image_urls.medium.replace('https://i.pximg.net', host()))]
            except:
                ERROR(traceback.format_exc())
                message += [img2qr(url, illust.image_urls.medium, headers={"Referer": "https://app-api.pixiv.net/"})]
    else:
        if illust.page_count > 1:
            imgs = [[page.image_urls.original, page.image_urls.medium] for page in illust.meta_pages]
        else:
            imgs = [[illust.meta_single_page.original_image_url, illust.image_urls.medium]]
        url = re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+', imgs[0][0]).group()
        try:message += [img2qr(fileserver +'/'+ b64encode('%d/%s_%d%s' % (time.time()-starttime+life, url, illust.page_count, imgs[0][0][-3:])), imgs[0][1].replace('https://i.pximg.net',host()))]
        except:message += [img2qr(fileserver +'/'+ b64encode('%d/%s_%d%s' % (time.time()-starttime+life, url, illust.page_count, imgs[0][0][-3:])), imgs[0][1], headers={"Referer": "https://app-api.pixiv.net/"})]
        if not (any(tag.name.lower() in ('r-18', 'r18', 'r-15', 'r15') for tag in illust.tags) and Group):
            message += [soup.Image(img[0].replace('https://i.pximg.net', host())) for img in imgs[:limit]]
    return message

def illust_node(illust, Type, target, sender=2854196310, name='QQ管家', Source=None): # 单插画聊天记录
    message = illust_msg(illust, Type=='Group')
    node = [soup.Node(sender, name, msg) for msg in message]
    for n in range(1, len(node), 50):
        error_number = 0
        while True:
            if n == 1:r = bot.SendMessage(Type, target, soup.Forward(*node[0:51], summary=f'总共{illust.page_count}张'))
            else:r = bot.SendMessage(Type, target, soup.Forward(*node[n:n+50], summary=f'总共{illust.page_count}张'))
            if r.code == 0 and r.msg == 'success' and r.messageId > 0:break # -1被吞、20禁言、30超长、400客户端错误、500服务端错误（超大、超量、下载失败）
            elif r.code == 20:break
            elif r.code == 500:pass
            if r.messageId == -1 or r.code == 30 or error_number == 1:
                node = [soup.Node(sender, name, msg) for msg in message[:2]]
            if error_number == 1:
                bot.SendMessage(Type, target, soup.Plain(f'⚠️Pid:{illust.id} 图床超时请等待⚠️'), id=Source)
            if error_number == 2:
                bot.SendMessage(Type, target, soup.Plain(f'🆘Pid:{illust.id} 发送失败🆘'), id=Source)
                break
            error_number += 1

def illusts_node(illusts, Group=True, limit=3): # 多插画聊天记录
    return [illust_msg(illust, Group ,limit) for illust in illusts]

def send_illusts(Type, target, Source, node, title=None):
    error_number = 0
    while node:
        r = bot.SendMessage(Type, target, soup.Forward(*node, title=title))
        if not r.code and r.msg == 'success' and r.messageId > 0:break
        elif r.code == 20:break
        elif r.code == 500:pass
        if r.messageId == -1 or r.code == 30 or error_number == 2:
            for n in node:
                if len(n.messageChain) > 1:
                    n.messageChain = [n.messageChain[0], n.messageChain[1]]
        if error_number == 2:
            bot.SendMessage(Type, target, soup.Plain('⚠️图床超时请等待⚠️'), id=Source)
        if error_number == 3:
            bot.SendMessage(Type, target, soup.Plain(f'🆘{title}发送失败🆘'), id=Source)
            break
        error_number += 1

def ranking(
        bot,
        targets:list|int=None,
        Type:str='Group', # 'Group'|'Friend'
        date:str=None, # 'YYYY-mm-dd'
        mode = 'day', # day, week, month, day_male, day_female, week_original, week_rookie, day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
        step = 20,
        stop = 40,
        title = None
    ):
    next_url = {'mode':mode, 'date':date}
    illusts = []
    while next_url:
        illust_ranking = pixiv.illust_ranking(**next_url)
        next_url = pixiv.parse_qs(illust_ranking.next_url)
        illusts += illust_ranking.illusts
        if len(illusts) >= stop:break
    if targets and type(targets) is not list:targets = [targets]
    else:targets = [g.id for g in bot.Group]
    if not targets:return
    illusts = [soup.Node(2854196310, 'QQ管家', *m) for m in illusts_node(illusts[:stop], True, 0)]
    for target in targets:
        for num in range(0,len(illusts),step):
            send_illusts(Type, target, None, illusts[num:num+step], title)
            time.sleep(10)
    for f in admin_ID():
        for num in range(0,len(illusts),step):
            send_illusts('Friend', f, None, illusts[num:num+step], title)
            time.sleep(10)

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

@QQBotSched(day_of_week=1) # 减少PID记录
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
def day_ranking(bot):
    ranking(bot, title=f'Pixiv {time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} 日榜单')

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
def day_r18_ranking(bot):
    ranking(bot, mode='day_r18',title=f'Pixiv {time.strftime("%Y-%m-%d", time.localtime(time.time()-86400))} R-18榜单')

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
def illust_follow(bot, date=None, Type=None, target=None):
    if date is None:date = time.strftime("%Y-%m-%d", time.localtime())
    next_url = {'restrict':'all'}
    illust_new = []
    while next_url:
        illusts = pixiv.illust_follow(**next_url)
        for illust in illusts.illusts:
            if illust.create_date[:10] > date:
                continue
            elif illust.create_date[:10] == date:
                illust_new.append(illust)
            else:
                illust,next_url = illust_new[0],None
                break
        if next_url:
            next_url = pixiv.parse_qs(illusts.next_url)
    if Type and target and Type.lower() in ['friend', 'group', 'temp']:
        imgqr = img2qr(fileserver+'/'+b64encode('%sx%s' % (password, 'x'.join([f'{hex(i.id)[2:]}' for i in illust_new]))),illust.image_urls.medium.replace('https://i.pximg.net',host()))
        bot.SendMessage(Type, target, soup.Plain(f'更新共 {len(illust_new)} 个作品'))
        bot.SendMessage(Type, target, imgqr)
        return
    imgqr = img2qr(fileserver+'/'+b64encode('%sx%s' % (password, 'x'.join([f'{hex(i.id)[2:]}' for i in illust_new]))),illust.image_urls.medium.replace('https://i.pximg.net',host()))
    for f in admin_ID():
        bot.SendMessage('Friend', f, soup.Plain(f'更新共 {len(illust_new)} 个作品'))
        bot.SendMessage('Friend', f, imgqr)
    imgqr = img2qr(fileserver+'/'+b64encode('%dx%s' % (time.time()-1672520400, 'x'.join([f'{hex(i.id)[2:]}' for i in illust_new]))),illust.image_urls.medium.replace('https://i.pximg.net',host()))
    for g in bot.Group:
        bot.SendMessage('Group', g.id, soup.Plain(f'更新共 {len(illust_new)} 个作品'))
        bot.SendMessage('Group', g.id, imgqr)

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
    if Type not in ['Friend','Group','Temp']:
        return

    Group = False
    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
        Group = True
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

    elif Plain.lower().strip().startswith('pid') or 'illust_id=' in Plain.replace('。','.') or 'artworks/' in Plain.replace('。','.'): # 通过PID获取插图
        Plain = Plain.replace('。','.')
        if Plain.strip().lower().startswith('pid'):
            try:pid = re.search(r'\d+', Plain)[0]
            except:
                bot.SendMessage(Type, target, soup.Plain('⚠️例:PID12345678'), id=Source.id)
                return
        elif 'illust_id=' in Plain:
            try:pid = re.search(r'illust_id=\d+', Plain)[0].replace('illust_id=', '')
            except:return
        elif 'artworks/' in Plain:
            try:pid = re.search(r'artworks/\d+', Plain)[0].replace('artworks/', '')
            except:return
        illust = pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMessage(Type, target, soup.Plain(f'⚠️{k}:{v}'+'\n'), id=Source.id) for k, v in illust.error.items() if v]
            return
        if not (illust.illust.title or illust.illust.user.name):
            bot.SendMessage(Type, target, soup.Plain(f'⚠️{Plain}已删除或非公开'), id=Source.id)
            return
        if illust.illust.type == 'ugoira':
            bot.SendMessage(Type, target, soup.Plain(f'♾️PixivID:{pid} 动图生成中♾️'), id=Source.id)
        else:
            bot.SendMessage(Type, target, soup.Plain(f'♾️PixivID:{pid} 获取中♾️'), id=Source.id)
        illusts = [illust.illust]

    elif Plain.lower().strip().startswith('uid') or 'member.php?' in Plain.replace('。','.') or 'users/' in Plain.replace('。','.'): # 通过UID获取用户作品
        Plain = Plain.replace('。','.')
        if Plain.lower().strip().startswith('uid'):
            try:uid = re.search(r'\d+', Plain)[0]
            except:
                bot.SendMessage(Type, target, soup.Plain('⚠️例:UID12345678'), id=Source.id)
                return
        elif 'member.php?' in Plain:
            try:uid = re.search(r'id=\d+', Plain)[0].replace('id=', '')
            except:return
        elif 'users/' in Plain:
            try:uid = re.search(r'users/\d+', Plain)[0].replace('users/', '')
            except:return
        bot.SendMessage(Type, target, soup.Plain(f'UserID:{uid} 获取中♾️'), id=Source.id)
        user = pixiv.user_detail(uid)
        if 'error' in user:
            [bot.SendMessage(Type, target, soup.Plain(f'⚠️{k}:{v}'+'\n')) for k, v in user.error.items() if v]
            return
        if 'https://i.pximg.net' in user.user.profile_image_urls.medium:message = soup.Image(user.user.profile_image_urls.medium.replace('https://i.pximg.net', host())),
        else:message = soup.Image(base64=content(user.user.profile_image_urls.medium)),
        message += soup.Plain(f"\nUid:{user.user.id}\n名字:{user.user.name}\n插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *message))
        admin_node.append(soup.Node(Sender.id, (hasattr(Sender, 'memberName') and Sender.memberName) or Sender.nickname, *message))
        illusts = pixiv.user_illusts(user.user.id).illusts[:10] + pixiv.user_illusts(user.user.id, 'manga').illusts[:10]
        illusts.sort(key=lambda i:i.create_date, reverse=True)
        illusts = illusts[:20] if Type=='Group' else illusts[:10]

    elif Plain.lower().strip().startswith(keyward) or (bot.conf.qq in At and any(kw for kw in keyward if kw in Plain.lower())): # 随机色图和搜索
        for kw in keyward:
            if kw in Plain:
                Plain = Plain.replace(kw, '').strip()
                break
        max_number = 10
        number = re.findall(r'\d+', Plain)
        if number and Plain == number[-1]:
            Plain = Plain.replace(number[-1], '').strip()
            number = int(number[-1])
        elif number and Plain.endswith(' '+number[-1]):
            Plain = Plain.replace(number[-1], '').strip()
            number = int(number[-1])
        else:
            number = 1
        illusts = []
        if Plain:
            bot.SendMessage(Type, target, soup.Plain(f'关键字：{Plain} 获取中♾️'), id=Source.id)
            bookmarks = [100000, 90000, 80000, 70000, 60000, 50000, 40000, 30000, 20000,10000, 5000, 1000, 500, 250, 100, 0]
            for bookmark in bookmarks:
                next_url = {'word':f'{Plain}{f" {bookmark}users入り"if bookmark else ""}'}
                while next_url:
                    p = pixiv.search_illust(**next_url)
                    next_url = pixiv.parse_qs(p.next_url)
                    if next_url:p.illusts.sort(key=lambda i:i.total_bookmarks, reverse=True)
                    else:break
                    for i in p.illusts:
                        if (i.total_bookmarks >= bookmark/2 >=50 or (250 >= bookmark and i.total_bookmarks >= 50)) and \
                            i.id not in pixiv.PID and \
                            i.page_count<=50:
                            illusts.append(i)
                            pixiv.PID.append(i.id)
                        if len(illusts) == number or len(illusts) == max_number:break
                    if len(illusts) == number or len(illusts) == max_number:break
                if len(illusts) == number or len(illusts) == max_number:break
            print([i.id for i in illusts])
            if not illusts:
                bot.SendMessage(Type, target, soup.Plain(f'没有"{Plain}"的相关结果，请考虑空格分割关键字或使用日语关键字:\n'+get_tags(20)), id=Source.id)
                return
        else:
            bot.SendMessage(Type, target, soup.Plain(f'{kw}获取中♾️'), id=Source.id)
            next_url = {"content_type":"illust"}
            while next_url:
                p = pixiv.illust_recommended(**next_url)
                next_url = pixiv.parse_qs(p.next_url)
                p.illusts.sort(key=lambda i:i.total_bookmarks, reverse=True)
                for i in p.illusts:
                    if i.id not in pixiv.PID:
                        illusts.append(i)
                        pixiv.PID.append(i.id)
                    if len(illusts) == number or len(illusts) == max_number:break
                if len(illusts) == number or len(illusts) == max_number:break

    else:return # 不匹配 PID UID 色图

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