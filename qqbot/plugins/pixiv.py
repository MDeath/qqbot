# -*- coding: utf-8 -*-

import json, os, time, re, traceback
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
from common import b64enc

password:str = '1064393873' # 不限时密钥
starttime = 1672531200 # 起始时间
life:int = 10800 # 链接时效 3*60*60
# 1672531200 - 10800 = 1672520400

fileserver = 'https://pixiv.mdie.top'

# 图片代理
HOSTS = [
    # 'i.pixiv.cat',
    'img.mdie.top',
    'i.pixiv.re',
    'i.pixiv.nl',
]
def change_host(url:str):
    # 图片代理
    HOSTS.append(HOSTS.pop(0))
    return url.replace('i.pximg.net',HOSTS[0])

# pixiv配置
config = {
    'REFRESH_TOKEN':'',
    'USERNAME':'',
    'PASSWORD':'',
    'PROXIES':{
        'http':'http://127.0.0.1:7897',
        'https':'http://127.0.0.1:7897'
    }
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

    def auth(self, username = None, password = None, refresh_token = None, headers = None):
        while True:
            try:return super().auth(username, password, refresh_token, headers)
            except PixivError as e:ERROR(e)

    def no_auth_requests_call(self, *args, **kwargs):
        while True:
            try:
                r = super().no_auth_requests_call(*args, **kwargs)
                if r.ok:return r
                if r.text:jsondict = self.parse_json(r.text)
                else:continue
                time.sleep(10)
                if hasattr(jsondict.error, 'message') and jsondict.error.message:
                    if 'Rate Limit' in jsondict.error.message:
                        continue
                    elif 'Error occurred at the OAuth process.' in jsondict.error.message:
                        self.auth(refresh_token=self.refresh_token or config['REFRESH_TOKEN'])
                        continue
                return r
            except PixivError as e:
                if e.reason.startswith('[ERROR] auth() failed! check refresh_token.') or str(e).startswith('Authentication required! Call login() or set_auth() first!'):
                    self.auth()
                elif e.reason.startswith('requests'):pass
                else:raise PixivError(e)
            except:
                traceback.print_exc()

pixiv = Pixiv(proxies=config['PROXIES'])

def get_tags(number=40):
    return "\n".join([f"{tag.tag}:{tag.translated_name}" for tag in pixiv.trending_tags_illust().trend_tags][:number]+['noai:禁用AI','r18:r-18'])

def content(url: str) -> bytes:
    with pixiv.requests.get(change_host(url), headers={"Referer": "https://app-api.pixiv.net/"}, stream=True) as response:return response.content

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
    if illust.illust_ai_type == 2:Plain += 'AI作图\n'
    for tag in illust.tags:Plain += f'{tag.name}:{tag.translated_name}\n'
    message = [soup.Text(Plain + f'总共{illust.page_count}张,链接时效三小时')]
    if illust.type == 'ugoira':
        if not os.path.exists(f'{tempdir}/{illust.id}.gif'):ugoira_download(illust)
        url = f"{fileserver}/{b64enc('%d'%(time.time()-starttime+life)+f'{tempdir}/{illust.id}.gif')}"
        for n in range(5):
            try:message += [img2qr(url, f'{tempdir}/{illust.id}.gif')]
            except:e = traceback.print_exception()
            else:break
        else:
            ERROR(e)
            for n in range(5):
                try:message += [img2qr(url, change_host(illust.image_urls.medium))]
                except:e = traceback.format_exc()
                else:break
            else:ERROR(e)
    else:
        if illust.page_count == 1:imgs = [[illust.meta_single_page.original_image_url, illust.image_urls.medium]]
        else:imgs = [[page.image_urls.original, page.image_urls.medium] for page in illust.meta_pages]
        url = re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+', imgs[0][0]).group()
        for n in range(5):
            try:message += [img2qr(fileserver +'/'+ b64enc('%d/%s_%d%s' % (time.time()-starttime+life, url, illust.page_count, imgs[0][0][-3:])), change_host(imgs[0][1]))]
            except:e = traceback.format_exc()
            else:break
        else:ERROR(e)
        if not Group:
            message += [soup.Image(change_host(img[0])) for img in imgs[:limit]]
    return message

def send_illust(illust, Type, target:int, reply:int=None): # 单插画聊天记录
    message = illust_msg(illust, Type=='group',8)
    node = [soup.Node(msg) for msg in message]
    error_number = 0
    while True:
        data = bot.SendMsg(Type, target, *node)
        error_number += 1
        if 'retcode' not in data:return data
        if error_number == 1:bot.SendMsg(Type, target, soup.Text(f'⚠️Pid:{illust.id} 图床超时请等待⚠️'), reply=reply)
        if error_number == 2:node = [soup.Node(msg) for msg in message[:2]] # 20002
        if error_number == 3:
            bot.SendMsg(Type, target, soup.Text(f'🆘Pid:{illust.id} 发送失败🆘'), reply=reply)
            break

def send_illusts(node, Type, target:int, reply:int=None, title=None):
    error_number = 0
    while node:
        data = bot.SendMsg(Type, target, *node)
        error_number += 1
        if 'retcode' not in data:return data
        if error_number == 1:bot.SendMsg(Type, target, soup.Text(f'⚠️图床超时请等待⚠️'), reply=reply)
        if error_number == 2:node = [soup.Node(*n.content[:2]) for n in node]
        if error_number == 3:
            bot.SendMsg(Type, target, soup.Text(f'🆘{title}发送失败🆘'), reply=reply)
            break

def ranking(
        bot,
        Type:str='group', # 'group'|'friend'
        targets:list|int=None,
        date:str=None, # 'YYYY-mm-dd'
        mode = 'day', # day, week, month, day_male, day_female, week_original, week_rookie, day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
        step = 40,
        stop = 100,
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
    if targets:targets = [getattr(bot,Type.title())(group_id=t,user_id=t) for t in targets]
    else:targets = [t for t in bot.Group()] if Type == 'group' else []
    if not targets:return
    targets = [t for t in bot.Friend(remark='Admin')] + targets
    illusts = [soup.Node(*illust_msg(illust, True, 0)) for illust in illusts[:stop]]
    data = [send_illusts(illusts[num:num+step], 'friend', targets[0].user_id, None, title) for num in range(0,len(illusts),step)]
    for target in targets[1:]:
        for num in range(0,len(illusts),step):
            send_illusts(illusts[num:num+step], 'group' if 'group_id' in target else 'friend', target.group_id if 'group_id' in target else target.user_id, None, title)

def illust_ranking(mode = "day", filter = "for_ios", date: str | None = None, total=100):
    next_url = {'mode':mode, 'date':date}
    illusts = []
    while next_url:
        illust_ranking = pixiv.illust_ranking(**next_url)
        next_url = pixiv.parse_qs(illust_ranking.next_url)
        illusts += illust_ranking.illusts
        if len(illusts) >= total:return illusts
    return illusts

def ranking(
        bot,
        mode = 'day', # day, week, month, day_male, day_female, week_original, week_rookie, day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
        date:str=None, # 'YYYY-mm-dd'
    ):
    if date is None:date = time.strftime("%Y-%m-%d", time.localtime())
    illusts = illust_ranking(mode,date=date)
    if hasattr(bot,'illusts') and isinstance(illusts,list):
        for illust in illusts:
            if [True for i in bot.illusts if i['pid']==illust.id]:continue
            bot.illusts.append({'uid':illust.user.id,'pid':illust.id,'type':illust.type,'count':illust.page_count,'medium':illust.image_urls.medium,'original':illust.meta_single_page.original_image_url if illust.page_count == 1 else illust.meta_pages[0].image_urls.original})
    text = 'x'+'x'.join([f'{hex(i.id)[2:]}' for i in illusts])
    imgqr = img2qr(fileserver+'/'+b64enc(password+text),change_host(illusts[0].image_urls.medium))
    for f in admin_ID():
        bot.SendMsg('friend', f.user_id, soup.Text(password+text))
        bot.SendMsg('friend', f.user_id, soup.Text(f'{date} 更新共 {len(illusts)} 个作品'))
        bot.SendMsg('friend', f.user_id, imgqr)
    imgqr = img2qr(fileserver+'/'+b64enc(f'{time.time()-1672520400}{text}'),change_host(illust.image_urls.medium))
    for g in bot.Group():
        bot.SendMsg('group', g.group_id, soup.Text(f'{date} 更新共 {len(illusts)} 个作品'))
        bot.SendMsg('group', g.group_id, imgqr)

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

    if config['REFRESH_TOKEN']:
        pixiv.set_auth(None, config['REFRESH_TOKEN'])
        pixiv.auth()
    elif config['USERNAME'] and config['PASSWORD']:
        pixiv.login(config['USERNAME'], config['PASSWORD'])

    if not hasattr(pixiv, 'PID') or pixiv.PID is None:
        try:
            if os.path.exists(bot.conf.Config('PID.json')):
                with open(bot.conf.Config('PID.json'), 'r', encoding='utf-8') as f:pixiv.PID = json.load(f) or []
            else:raise
        except:
            pixiv.PID = []
            with open(bot.conf.Config('PID.json'),'w', encoding='utf-8') as f:json.dump(pixiv.PID, f)

def onUnplug(bot):
    del bot.pixiv

def onInterval(bot): # 刷新令牌和保存PID记录
    with open(bot.conf.Config('PID.json'), 'w', encoding='utf-8') as f:json.dump(pixiv.PID, f)

@QQBotSched(day_of_week=1) # 每周一减少PID记录
def week_clear_pid(bot):
    pixiv.PID = pixiv.PID[-10000:]

# Pixiv日榜
# @QQBotSched(hour=8)
def day_ranking(bot):
    ranking(bot)

# Pixiv R-18日榜
# @QQBotSched(hour=23, minute=30)
def day_r18_ranking(bot):
    ranking(bot, mode='day_r18')

# Pixiv每日动态
@QQBotSched(hour=23)
def illust_follow(bot, Type=None, target=None, date=None):
    if date is None:date = time.strftime("%Y-%m-%d", time.localtime())
    next_url = {'restrict':'all'}
    illust_list = []
    while next_url:
        illusts = pixiv.illust_follow(**next_url)
        for illust in illusts.illusts:
            if illust.create_date[:10] > date:
                continue
            elif illust.create_date[:10] == date:
                illust_list.append(illust)
            else:
                next_url = None
                break
        if next_url:
            next_url = pixiv.parse_qs(illusts.next_url)
    illusts = illust_list.copy()
    illusts.reverse()
    illust_list.sort(key=lambda i:i.total_bookmarks/i.total_view)
    illust = illust_list[-1]
    for illust in illusts:
        bot.illusts.append({'uid':illust.user.id,'pid':illust.id,'type':illust.type,'count':illust.page_count,'medium':illust.image_urls.medium,'original':illust.meta_single_page.original_image_url if illust.page_count == 1 else illust.meta_pages[0].image_urls.original})
    text = 'x'+'x'.join([f'{hex(i.id)[2:]}' for i in illusts])
    imgqr = img2qr(fileserver+'/'+b64enc(password+text),change_host(illust.image_urls.medium))
    if Type and target and Type in ['friend', 'group']:
        bot.SendMsg(Type, target, soup.Text(password+text))
        bot.SendMsg(Type, target, soup.Text(f'{date} 更新共 {len(illusts)} 个作品'))
        bot.SendMsg(Type, target, imgqr)
        return
    
    for f in admin_ID():
        bot.SendMsg('friend', f.user_id, soup.Text(password+text))
        bot.SendMsg('friend', f.user_id, soup.Text(f'{date} 更新共 {len(illusts)} 个作品'))
        bot.SendMsg('friend', f.user_id, imgqr)
    imgqr = img2qr(fileserver+'/'+b64enc(f'{time.time()-1672520400}{text}'),change_host(illust.image_urls.medium))
    for g in bot.Group():
        bot.SendMsg('group', g.group_id, soup.Text(f'{date} 更新共 {len(illusts)} 个作品'))
        bot.SendMsg('group', g.group_id, imgqr)

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

    Group = 'group' == Type
    Images = []
    Plain = ''
    for msg in Message:
        if msg.type == 'text':Plain += msg.text
        if msg.type == 'image':Images.append(msg)
        if msg.type == 'reply':
            try:Message += [m for m in bot.GetMsg(msg.id).message if m.type == 'image']
            except:pass

    node = []
    admin_node = []
    keyword = ('st', 'setu', '色图', '涩图', '瑟图', '来点色图', '来点瑟图', '来点涩图')

    if Plain == '推荐关键字' or Plain == '关键字推荐':
        bot.SendMsg(Type, Source.target, soup.Text(get_tags()), reply=Source.message_id)
        return

    if Plain.lower().strip().startswith('pid') or 'illust_id=' in Plain or 'artworks/' in Plain or len(re.findall(r'/(\d+){1,7}',Plain)) == 7: # 通过PID获取插图
        if Type == 'group':bot.Reaction(Source.target,Source.message_id,424)
        for format in [r'illust_id=(\d+)',r'/(\d+)',r'\d+']:
            try:pid = re.findall(format,Plain)[-1]
            except:pass
            else:break
        else:
            bot.SendMsg(Type, Source.target, soup.Text('⚠️例:PID12345678'), reply=Source.message_id)
            return
        illust = pixiv.illust_detail(pid)
        if 'error' in illust:
            [bot.SendMsg(Type, Source.target, soup.Text(f'Pid:{pid}\n⚠️{k}:{v}'), reply=Source.message_id) for k, v in illust.error.items() if v]
            return
        if not (illust.illust.title or illust.illust.user.name):
            bot.SendMsg(Type, Source.target, soup.Text(f'⚠️{Plain}已删除或非公开'), reply=Source.message_id)
            return
        
        if illust.illust.type == 'ugoira':
            bot.SendMsg(Type, Source.target, soup.Text(f'♾️PixivID:{pid},Title:{illust.illust.title} 动图生成中♾️'), reply=Source.message_id)
        else:
            bot.SendMsg(Type, Source.target, soup.Text(f'♾️PixivID:{pid},Title:{illust.illust.title} 获取中♾️'), reply=Source.message_id)
        illusts = [illust.illust]

    elif Plain.lower().strip().startswith('uid') or 'member.php?' in Plain or 'users/' in Plain: # 通过UID获取用户作品
        if Type == 'group':bot.Reaction(Source.target,Source.message_id,424)
        try:
            if Plain.lower().strip().startswith('uid'):
                uid = re.search(r'\d+', Plain)[0]
            elif 'member.php?' in Plain:
                uid = re.search(r'id=\d+', Plain)[0].replace('id=', '')
            elif 'users/' in Plain:
                uid = re.search(r'users/\d+', Plain)[0].replace('users/', '')
        except:
            bot.SendMsg(Type, Source.target, soup.Text('⚠️例:UID12345678'), reply=Source.message_id)
            return
        user = pixiv.user_detail(uid)
        if 'error' in user:
            [bot.SendMsg(Type, Source.target, soup.Text(f'⚠️{k}:{v}'+'\n'), reply=Source.message_id) for k, v in user.error.items() if v]
            return
        bot.SendMsg(Type, Source.target, soup.Text(f'UserID:{uid},Name:{user.user.name} 获取中♾️'), reply=Source.message_id)
        if 'https://i.pximg.net' in user.user.profile_image_urls.medium:message = soup.Image(change_host(user.user.profile_image_urls.medium)),
        else:message = soup.Image(content(user.user.profile_image_urls.medium)),
        message += soup.Text(f"\nUid:{user.user.id}\n名字:{user.user.name}\n插画:{user.profile.total_illusts} 漫画:{user.profile.total_manga} 小说:{user.profile.total_novels}"),
        node.append(soup.Node(*message))
        admin_node.append(soup.Node(*message))
        illusts = pixiv.user_illusts(user.user.id).illusts + pixiv.user_illusts(user.user.id, 'manga').illusts
        illusts.sort(key=lambda i:i.create_date, reverse=True)
        illusts = illusts[:20] if Type=='group' else illusts[:10]

    elif Plain.lower().strip().startswith(keyword) and not Images: # 随机色图和搜索
        if Type == 'group':bot.Reaction(Source.target,Source.message_id,424)
        for kw in keyword:
            if kw in Plain.lower():
                tags = Plain.lower().replace(kw, '').strip()
                break
        noai, r18 = any([keyword in tags.lower() for keyword in ['noai','禁用AI']]), any([keyword in tags.lower() for keyword in ['r18','r-18']])
        for kw in ('noai','禁用AI'):tags = tags.lower().replace(kw,'')
        number = 1
        avgs = tags.split()
        if avgs and avgs[-1].isdigit():
            tags = tags.replace(avgs[-1],'').strip()
            number = 10 if int(avgs[-1]) > 10 else int(avgs[-1])
        illusts = []
        if tags:
            bot.SendMsg(Type, Source.target, soup.Text(f'关键字：{tags} 获取中♾️'), reply=Source.message_id)
            bookmarks = [100000, 90000, 80000, 70000, 60000, 50000, 40000, 30000, 20000,10000, 5000, 1000, 500, 250, 100, 0]
            for bookmark in bookmarks:
                next_url = {'word':f'{tags}{f" {bookmark}users入り"if bookmark else ""}'}
                while next_url:
                    p = pixiv.search_illust(**next_url)
                    next_url = pixiv.parse_qs(p.next_url)
                    if next_url:p.illusts.sort(key=lambda i:i.total_bookmarks, reverse=True)
                    else:break
                    for i in p.illusts:
                        if (noai and i.illust_ai_type == 2) or (not r18 and i.x_restrict):continue
                        if (i.total_bookmarks >= bookmark/2 >=50 or (250 >= bookmark and i.total_bookmarks >= 50)) and \
                            i.id not in pixiv.PID and \
                            i.page_count<=50:
                            illusts.append(i)
                            pixiv.PID.append(i.id)
                        if len(illusts) == number:break
                    if len(illusts) == number:break
                if len(illusts) == number:break
            if not illusts:
                bot.SendMsg(Type, Source.target, soup.Text(f'没有"{tags}"的相关结果，请考虑空格分割关键字或使用日语关键字:\n'+get_tags(20)), reply=Source.message_id)
                return
        else:
            bot.SendMsg(Type, Source.target, soup.Text(f'{kw}获取中♾️'), reply=Source.message_id)
            next_url = {"content_type":"illust"}
            while next_url:
                p = pixiv.illust_recommended(**next_url)
                next_url = pixiv.parse_qs(p.next_url)
                p.illusts.sort(key=lambda i:i.total_bookmarks, reverse=True)
                for i in p.illusts:
                    if (noai and i.illust_ai_type == 2) or (not r18 and i.x_restrict):continue
                    if i.id not in pixiv.PID:
                        illusts.append(i)
                        pixiv.PID.append(i.id)
                    if len(illusts) == number:break
                if len(illusts) == number:break

    else:return # 不匹配 PID UID 色图

    if len(illusts) == 1:
        send_illust(illusts[0], Type, Source.target, Source.message_id)
        if Sender.user_id in [f.user_id for f in admin_ID()]:return
        for f in admin_ID():
            bot.SendMsg('friend', f.user_id, soup.Text(f'群 {Source.group_name}({Source.group_id}) 成员 {Sender.nickname}({Sender.user_id}): {Plain}' if Group else f'好友 {Sender.nickname}({Sender.user_id}): {Plain}'))
            send_illust(illusts[0], 'friend', f.user_id)
        return

    send_illusts([soup.Node(*illust_msg(illust, Group, 3)) for illust in illusts], Type, Source.target, Source.message_id)
    if Sender.user_id in [f.user_id for f in admin_ID()]:return
    for f in admin_ID():
        bot.SendMsg('friend', f.user_id, soup.Text(f'群 {Source.group_name}({Source.group_id}) 成员 {Sender.nickname}({Sender.user_id}): {Plain}' if Group else f'好友 {Sender.nickname}({Sender.user_id}): {Plain}'))
        send_illusts([soup.Node(*illust_msg(illust, False, 3)) for illust in illusts], 'friend', f.user_id)