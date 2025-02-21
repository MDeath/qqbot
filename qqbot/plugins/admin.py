# -*- coding: utf-8 -*-

import os,json,psutil,random,time,traceback

from qqbotcls import QQBotSched,bot
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING, SetLogLevel, EnableLog, DisableLog
from mainloop import Put, PutBack
from common import JsonDict, DotDict, secs2hours, B2B, b64dec, b64enc, jsondumps, jsonloads, SGR
import soup

def admin_ID(user=False,me=False) -> list:
    return [f for f in bot.Friend() if f.user_remark=='Admin' or (user and f.user_remark=='User') or (me and f.user_id==bot.qq)]

def system_status():
    m = psutil.virtual_memory()
    b = psutil.sensors_battery()
    l = [
        f'CPU:{psutil.cpu_percent()}%',
        f'内存:{m.percent}% ，{B2B(m.used)}/{B2B(m.total)}'
    ]
    if b:l.append(f'电源:{b.percent}% {f"，充电中🔋" if b.power_plugged else f"{secs2hours(b.secsleft)}"}')
    return '\n'.join(l)

CallBackList = []

# @QQBotSched(year=None, 
#             month=None, 
#             day=None, 
#             week=None, 
#             day_of_week=None, 
#             hour=None, 
#             minute=','.join([str(n) for n in range(0,60,10)]),
#             second=30, 
#             start_date=None, 
#             end_date=None, 
#             timezone=None)
def Chime(bot):
    '定时任务'
    for f in admin_ID():
        if random.randint(0,1):bot.SendMsg('friend',f.user_id,soup.Text(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())),recall=90000)
        else:bot.SendMsg('friend',f.user_id,soup.Text(time.strftime('%Y%m%d %H%M%S',time.localtime())),recall=90000)

def onPlug(bot):
    bot.battery = psutil.sensors_battery()
    bot.battery = bot.battery.percent if bot.battery else None

def onUnplug(bot):
    '''\
    此插件不可卸载'''
    bot.Plug(__name__)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    输入指令使用
    -=# 一般权限 #=-
    菜单
    更新联系人
    插件列表
    说明(可附带插件名)
    whoisyourdaddy
    -=# 管理员权限 #=-
    加载插件《插件名》
    卸载插件《插件名》
    -=# 超级权限 #=-
    关机 重启 
    命令行前置符 #'''

    DEBUG(f'Type: {Type}, Sender: {Sender}, Source: {Source}, Message: {Message}')

    At = []
    Text = ''
    Image = []
    Flash = None
    for msg in Message:                                             # 描述              构建
        if msg.type == 'reply':                                     # 回复对象          soup.Reply(id:int)
            try:Reply = bot.GetMsg(msg.id)
            except:pass
        if msg.type == 'text':Text += msg.text                      # 文本对象          soup.Text(text:str)
        if msg.type == 'at':At.append(msg.qq)                       # AT对象            soup.At(uid:int='all')
        if msg.type == 'face':pass                                  # 表情对象          soup.Face(id:int, big=None|bool)
        if msg.type == 'bubble_face':pass                           # 连击表情对象      soup.FaceCount(id:int, count:bool=None)
        if msg.type == 'image':Image.append(msg)                    # 图片对象          soup.Image(file:str|bytes|'http://'|'https://'|'file://'|'base64://',type=None|'show'|'flash'|'original',subType=0~4|7~10|13)
        if msg.data_type == 'flash':Flash = msg                     # 闪图对象          soup.Image(file:str|bytes, type='flash')
        if msg.type == 'record':Voice = msg                         # 语音对象          soup.Voice(file:str|bytes)
        if msg.type == 'video':Video = msg                          # 语音对象          soup.Video(file:str|bytes)
        if msg.type == 'basketball':Basketball = msg.id             # 篮球表情对象      soup.Basketball(id:int)
        if msg.type == 'new_rps':RPS = msg.id                       # 石头剪刀布对象    soup.RPS(id:int)
        if msg.type == 'new_dice':Dice = msg.id                     # 骰子对象          soup.Dice(id:int)
        if msg.type == 'poke':Poke = msg                            # 戳一戳对象        soup.Poke(uid:int,type:int=1,level:int=1)
        if msg.type == 'touch':Touch = msg = id                     # 拍一拍对象        soup.Touch(uid:int)
        if msg.type == 'music':Music = msg                          # 音乐分享对象      soup.Music(url:str=None,audio:str=None,title:str=None,singer:str=None,image:str=None,type:str=None, id:int=None)
        if msg.type == 'weather':Weather = msg                      # 天气对象          soup.Weather(city:str=None,code:str=None)
        if msg.type == 'location':Location = msg                    # 位置对象          soup.Location(lat:float, lon:float, title:str=None, content:str=None)
        if msg.type == 'share':Share = msg                          # 分享连接对象      soup.Url(url:str,title:str=None,content:str=None,file:str=None)
        if msg.type == 'gift':Gift = msg                            # 礼物对象          soup.Gift(uid:int,id:id)
        if msg.type == 'forward':Forward = bot.GetForward(msg.id)   # 合并转发对象
        if msg.type == 'Json':Json = jsonloads(msg.data)            # json对象          Json(obj:object)

    reply = lambda *msg, reply=None, recall=None:bot.SendMsg(Type,Source.target,*msg,reply=reply,recall=recall)

    if Text == 'whoisyourdaddy':reply(soup.Text(f'is '),soup.At(1064393873), reply=Source.message_id)

    if Text.startswith(('$', '￥', '#')):
        try:
            if Sender.user_id in [f.user_id for f in admin_ID(me=True)] and Text[1:]:rt, err = eval(Text[1:]), None
            else:rt, err = system_status(), None
        except:
            rt, err = None, traceback.format_exc()
        if Text.startswith('#'):
            reply(soup.Text(rt or err), reply=Source.message_id)
        else:
            if err is None:
                INFO(f'\n{rt}')
            else:
                ERROR(f'\n{err}')
        return

    if bot.OneBot.qq in At:[bot.SendMsg('Friend',f.user_id,soup.Text(f"[@ME] 群 {Source.group_name}({Sender.group_id}) 成员 {Sender.nickname}({Sender.user_id}) @ME:\n"),*[msg if msg.type!='At' else soup.Text(f"{(msg.id==bot.OneBot.qq and '[@ME]')or f'@{msg.qq}'}") for msg in Message])for f in admin_ID()]

    if Flash:[bot.SendMsg(Type,f.user_id,soup.Text(((Type == 'group' and f'群 {Source.group_name}({Sender.group_id}) 成员 {Sender.nickname}({Sender.user_id}') or f'好友 {Sender.nickname}({Sender.user_id}')+') 的闪图：\n'),soup.Image(Flash.url))for f in admin_ID]

    plug = [m.split('.')[0] for m in os.listdir(bot.conf.pluginPath)]

    if Text.strip() in ['菜单','帮助','help','memu']:
        message = '已加载模块菜单'
        for module in bot.plugins.values():
            if hasattr(module, 'onQQMessage') and module.onQQMessage.__doc__:
                message += f'\n-=# {module.__name__} 模块 #=-\n{module.onQQMessage.__name__}\n{module.onQQMessage.__doc__}\n'
        reply(soup.Text(message), reply=Source.message_id)
        return

    elif Text.strip().startswith('说明'):
        moduleName = Text.replace('说明','',1).strip()
        if moduleName != '' and moduleName in bot.Plugins():
            message = moduleName+' 说明'
            modules = [bot.plugins[moduleName]]
        elif moduleName != '' and moduleName not in bot.Plugins():
            message = moduleName+' 说明(未加载)'
            try:
                modules = [__import__(moduleName)]
            except:
                reply(soup.Text(f'❌未找到 {moduleName}'), reply=Source.message_id)
                return
        elif moduleName == '':
            message = '已加载模块说明'
            modules = bot.plugins.values()
        else:
            return
        for module in modules:
            msg = ''
            for slotName in bot.slotsTable.keys():
                if hasattr(module, slotName):
                    mod = getattr(module,slotName)
                    if mod.__doc__:
                        msg += f'\n{mod.__name__}\n{mod.__doc__}\n'
            if msg:
                message += f'\n-=# {module.__name__} 模块 #=-{msg}'
        return reply(soup.Text(message), reply=Source.message_id)

    elif Text.lower() in ['插件列表','plugins']:
        for p in plug:
            if p.startswith('_'):
                continue
            elif p in bot.Plugins():
                Text += f'\n🔳已加载 {p}'
            else:
                Text += f'\n⬜未加载 {p}'
        reply(soup.Text(Text), reply=Source.message_id)
        return

    if any([Sender.user_id == f.user_id for f in admin_ID(False,True)]):

        if Text.lower().strip().startswith(('加载插件', 'plug')):
            moduleName = Text.lower().strip()
            for keyword in ['加载插件','plug']:moduleName = moduleName.replace(keyword,'')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m:
                    result = bot.Plug(m)
                    reply(soup.Text(result), reply=Source.message_id)
            return

        if Text.lower().strip().startswith(('卸载插件', 'unplug')):
            moduleName = Text.lower().strip()
            for keyword in ['卸载插件','unplug']:moduleName = moduleName.replace(keyword,'')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m:
                    result = bot.Unplug(m)
                    reply(soup.Text(result), reply=Source.message_id)
            return

        if Text.lower().strip().startswith(('日志等级', 'setloglevel')):
            for keyword in ['日志等级', 'setloglevel']:Text = Text.replace(keyword,'')
            SetLogLevel(Text)
            reply(soup.Text(f'日志等级设置为 {Text.upper()}'), reply=Source.message_id)
            return

        if Text.lower().strip().startswith(('启用日志', 'enlog')):
            EnableLog()
            reply(soup.Text('日志已启用'), reply=Source.message_id)
            return

        if Text.lower().strip().startswith(('禁用日志', 'dislog')):
            DisableLog()
            reply(soup.Text('日志已禁用'), reply=Source.message_id)
            return

        if Text.strip().lower() in ['重启', 'rebot', 'reboot', 'restart', 'reset']:
            reply(soup.Text('bot正在重启'), reply=Source.message_id)
            Put(bot.Restart)
            return

        if Text.strip().lower() in ['关机','stop','exit','quit']:
            reply(soup.Text('bot以关闭'), reply=Source.message_id)
            Put(bot.Stop)
            return

def onQQNotice(bot, Notice):
    '''\
    事件处理'''
    if Notice.notice_type == 'group_upload': # 群文件上传
        {'time': 1736753531, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_upload', 'group_id': 714470571, 'operator_id': 1535559131, 'user_id': 1535559131, 'file': {'id': '/3f16b76c-7d92-4729-990d-bd2b3d791cba', 'name': 'base.apk.1', 'size': 38357089, 'busid': 102, 'url': 'http://gzc-download.ftn.qq.com/ftn_handler/c8107a6ddd20e4068832ded5982318a73b913bbcf8cdba24ddf4ea8f36eb7cd2e5bc801511f571ce4a2a227285d2b96e406f5be10f812622764bb28cc88a2312/?fname=/3f16b76c-7d92-4729-990d-bd2b3d791cba&client_proto=qq&client_appid=537228697&client_type=android&client_ver=9.0.71&client_down_type=auto&client_aio_type=unk'}, 'source': 'private'}
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        group = bot.group(group_id=Notice.group_id)[0]
        for f in admin_ID():
            bot.SendMsg('friend',f.user_id,soup.Text(f'群友 {member.nickname}({member.user_id}) 在 {group.group_name}({group.group_id}) 上传了文件:\n{Notice.file.name}\nID:{Notice.file.id}\n大小:{B2B(Notice.file.size)}\n链接:{Notice.file.url}'))
        return
    
    if Notice.notice_type == 'group_admin': # 群管理员变动
        pass

    if Notice.notice_type == 'group_decrease': # 群成员减少
        {'time': 1737420071, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_decrease', 'sub_type': 'leave', 'group_id': 931021429, 'operator_id': 0, 'user_id': 3112904250, 'user_uid': 'u_hONp9jR8QqCd91_yRgDuHw', 'sender_id': 0, 'target_id': 3112904250, 'target_uid': 'u_hONp9jR8QqCd91_yRgDuHw', 'source': 'group'}
        bot.SendMsg('group',Notice.group_id,soup.Text(f'{Notice.user_id} 离开了，永远缅怀'),soup.Face(9))
        group = bot.Group(group_id=Notice.group_id)[0]
        for f in admin_ID():
            bot.SendMsg('friend',f.user_id,soup.Text(f'{Notice.user_id} 退出了 {group.group_name}({group.group_id})'))

    if Notice.notice_type == 'group_increase': # 群成员增加
        {'time': 1737431992, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_increase', 'sub_type': 'approve', 'group_id': 683327278, 'operator_id': 183744529, 'operator_uid': 'u_mEg0pkdNJZBsh5PmiJtZBw', 'user_id': 2117636781, 'user_uid': 'u_Hd9dRGd0SK2L0lS-5rUX_Q', 'sender_id': 183744529, 'target_id': 2117636781, 'target_uid': 'u_Hd9dRGd0SK2L0lS-5rUX_Q', 'source': 'group'}
        bot.SendMsg('group',Notice.group_id,soup.Text('欢迎新人'),soup.Face(13),soup.At(Notice.user_id))
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        group = bot.group(group_id=Notice.group_id)[0]
        for f in admin_ID():
            bot.SendMsg('friend',f.user_id,soup.Text(f'{member.nickname}({member.user_id}) 加入了 {group.group_name}({group.group_id})'))

    if Notice.notice_type == 'group_ban': # 群禁言
        group = bot.Group(group_id=Notice.group_id)[0]
        user = bot.Member(group_id=Notice.group_id,user_id=Notice.operator_id)[0]
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        if Notice.sub_type == 'ban': # 禁言
            {'time': 1733392512, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_ban', 'sub_type': 'ban', 'group_id': 260715723, 'operator_id': 1064393873, 'operator_uid': 'u_FHYadP-ArAm1UC9BAgy-6w', 'user_id': 2907237958, 'sender_id': 1064393873, 'duration': 600, 'target_id': 2907237958, 'target_uid': 'u_XGLNBZyp3QKeaXiEqaWQjw', 'source': 'group'}
            bot.SendMsg('group',Notice.group_id,soup.At(Notice.user_id),soup.Text('你倒是说句话呀'),soup.Face(13))
            for f in admin_ID():bot.SendMsg('Friend',f.user_id,soup.Text(f'群 {group.group_name}({group.group_id}) 成员 {member.nickname}({member.user_id}) 被 {user.nickname}[{user.role}({user.user_id})] 禁言至 {time.strftime(f"%y-%m-%d %H:%M",time.localtime(Notice.time+Notice.duration))}'))

        else:# 解禁
            {'time': 1733392755, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_ban', 'sub_type': 'lift_ban', 'group_id': 260715723, 'operator_id': 1064393873, 'operator_uid': 'u_FHYadP-ArAm1UC9BAgy-6w', 'user_id': 2907237958, 'sender_id': 1064393873, 'duration': 0, 'target_id': 2907237958, 'target_uid': 'u_XGLNBZyp3QKeaXiEqaWQjw', 'source': 'group'}
            bot.SendMsg('group',Notice.group_id,soup.Text('啧，走后门'))
            for f in admin_ID():bot.SendMsg('Friend',f.user_id,soup.Text(f'群 {group.group_name}({group.group_id}) 成员 {member.nickname}({member.user_id}) 被 {user.nickname}[{user.role}({user.user_id})] 解除禁言'))
        return
    
    if Notice.notice_type == 'group_recall': # 群消息撤回
        group = bot.Group(group_id=Notice.group_id)[0]
        user = bot.Member(group_id=Notice.group_id,user_id=Notice.operator_id)[0]
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        for f in admin_ID():
            bot.SendMsg('friend', f.user_id, soup.Text(f'群 {group.group_name}({group.group_id}) {user.nickname}[{user.role}({user.user_id})] 撤回了 {"" if user.user_id==member.user_id else f" {member.nickname}[{member.role}({member.user_id})] 的"}消息ID {Notice.message_id}'))
            if 'msglog' in bot.db.Table:
                message = bot.db.Select('msglog','message_id',Notice.message_id)
                if message:bot.SendMsg('friend', f.user_id, *[soup.Node(*msg.message) for msg in message])
        return
    
    if Notice.notice_type == 'group_card': # 群成员名片变动
        pass
    if Notice.notice_type == 'friend_add': # 好友添加
        pass
    if Notice.notice_type == 'friend_recall': # 好友撤回
        for f in admin_ID():
            bot.SendMsg('friend', f.user_id, soup.Text(f'好友{bot.Friend(user_id=Notice.operator_id)[0].nickname}[{bot.Friend(user_id=Notice.operator_id)[0].user_remark}({bot.Friend(user_id=Notice.operator_id)[0].user_id})]撤回了消息 {Notice.message_id}'))
            if 'msglog' in bot.db.Table:
                message = bot.db.Select('msglog','message_id',Notice.message_id)
                if message:bot.SendMsg('friend', f.user_id, *[soup.Node(*msg.message) for msg in message])
        return
    if Notice.notice_type == 'offline_file': # 接收到离线文件包
        pass
    if Notice.notice_type == 'client_status': # 客户端状态
        pass
    if Notice.notice_type == 'essence': # 精华消息
        {'time': 1733382566, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'essence', 'sub_type': 'add', 'group_id': 683327278, 'operator_id': 183744529, 'sender_id': 592066232, 'message_id': 971594782, 'source': 'group'}
        group = bot.Group(group=Notice.group_id)
        user = bot.Member(group=Notice.group_id,user_id=Notice.operator_id)
        member = bot.Member(group=Notice.group_id,user_id=Notice.sender_id)
        message = bot.GetMsg(Notice.message_id)
        for f in admin_ID():
            if Notice.sub_type == 'add':
                bot.SendMsg('friend',f.user_id,soup.Text(f'群 {group.group_name}({group.group_id}) 成员 {member.nickname}({member.user_id}) 的消息 ({Notice.message_id}) 被 {user.nickname}[{user.role}({user.user_id})] 添加精华'))
                bot.SendMsg('friend',f.user_id,soup.Node(id=Notice.message_id))
            else:
                bot.SendMsg('friend',f.user_id,soup.Text(f'群 {group.group_name}({group.group_id}) 成员 {member.nickname}({member.user_id}) 的消息 ({Notice.message_id}) 被 {user.nickname}[{user.role}({user.user_id})] 移出精华'))
                bot.SendMsg('friend',f.user_id,soup.Node(id=Notice.message_id))

    if Notice.notice_type == 'notify': # 系统通知
        if Notice.sub_type == 'honor': # 群荣誉变更
            pass
        if Notice.sub_type == 'poke': # 戳一戳
            pass
        if Notice.sub_type == 'lucky_king': # 运气王
            pass
        if Notice.sub_type == 'title': # 群头衔变更
            pass
    for f in admin_ID():bot.SendMsg('friend', f.user_id,soup.Text(Notice))
    return
    first = True
    t = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())
    for f in admin_ID():
        try:
            if Event.type == 'BotOnlineEvent': # Bot登录成功
                bot.SendMsg('Friend',f,soup.Text(f'{t} {Event.qq} 登陆成功'))
            elif Event.type == 'BotOfflineEventActive': # Bot主动离线
                bot.Mirai.bind()
                bot.SendMsg('Friend',f,soup.Text(f'{t} {Event.qq} 主动离线'))
            elif Event.type == 'BotOfflineEventForce': # Bot被挤下线
                bot.Mirai.bind()
                bot.SendMsg('Friend',f,soup.Text(f'{t} {Event.qq} 被挤下线'))
            elif Event.type == 'BotOfflineEventDropped': # Bot被服务器断开或因网络问题而掉线
                os.popen('taskkill /f /im java.exe').read() # 干掉Mirai进程，需要MCL启动脚循环自启，本配合自动登录
                bot.Mirai.bind()
                bot.SendMsg('Friend',f,soup.Text(f'{t} {Event.qq} 被服务器断开或因网络问题而掉线'))
            elif Event.type == 'BotReloginEvent': # Bot主动重新登录
                bot.Mirai.bind()
                bot.SendMsg('Friend',f,soup.Text(f'{t} {Event.qq} 主动重新登录'))
            elif Event.type == 'FriendInputStatusChangedEvent': # 好友输入状态改变
                pass # bot.SendMsg('Friend',f,soup.Text(f'好友 {Event.friend.nickname}[{Event.friend.remark}({Event.friend.id})] {((Event.inputting and "正在输入") or "取消输入")}'))
            elif Event.type == 'FriendNickChangedEvent': # 好友昵称改变
                bot.SendMsg('Friend',f,soup.Text(f'好友 {Event.friend.nickname}[{Event.friend.remark}({Event.friend.id})] 昵称改为 {Event.to}'))
            elif Event.type == 'BotGroupPermissionChangeEvent': # Bot在群里的权限被改变. 操作人一定是群主
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) 权限由 {Event.origin} 改为 {Event.current}'))
            elif Event.type == 'BotMuteEvent': # Bot被禁言
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.operator.group.name}({Event.operator.group.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 禁言 {secs2hours(Event.durationSeconds)}'))
            elif Event.type == 'BotUnmuteEvent': # Bot被取消禁言
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.operator.group.name}({Event.operator.group.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 解禁'))
            elif Event.type == 'BotJoinGroupEvent': # Bot加入了一个新群
                bot.SendMsg('Friend',f,soup.Text(f'加入 {Event.group.name}({Event.group.id}) 群'))
            elif Event.type == 'BotLeaveEventActive': # Bot主动退出一个群
                bot.SendMsg('Friend',f,soup.Text(f'退出 {Event.group.name}({Event.group.id}) 群'))
            elif Event.type == 'BotLeaveEventKick': # Bot被踢出一个群
                bot.SendMsg('Friend',f,soup.Text(f'被踢出 {Event.group.name}({Event.group.id}) 群'))
            elif Event.type == 'BotLeaveEventDisband': # Bot因群主解散群而退出群, 操作人一定是群主
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) 被解散'))
            elif Event.type == 'GroupRecallEvent': # 群消息撤回
                bot.SendMsg('Friend',f,soup.Forward(soup.Node(ref=[Event.group.id,Event.messageId])))
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 撤回了 {Event.authorId} 的消息ID {Event.messageId}'))
            elif Event.type == 'FriendRecallEvent': # 好友消息撤回
                bot.SendMsg('Friend',f,soup.Forward(soup.Node(ref=[Event.authorId,Event.messageId])))
                bot.SendMsg('Friend',f,soup.Text(f'好友 {Event.authorId} 撤回了消息ID {Event.messageId}'))
            elif Event.type == 'NudgeEvent': # 戳一戳事件
                if Event.target==bot.conf.qq:bot.SendMsg('Friend',f,soup.Text(f'{(Event.subject.kind=="Group" and "群") or "好友"}({Event.fromId}) 戳了戳 {Event.target} 的脸'))
            elif Event.type == 'GroupNameChangeEvent': # 某个群名改变
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.origin}({Event.group.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 改成 {Event.current}'))
            elif Event.type == 'GroupEntranceAnnouncementChangeEvent': # 某群入群公告改变
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) 公告:\n{Event.origin}\n被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 改为:\n{Event.current}'))
            elif Event.type == 'GroupMuteAllEvent': # 全员禁言
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] {(Event.current and "开启了全员禁言")or "关闭了全员禁言"}'))
            elif Event.type == 'GroupAllowAnonymousChatEvent': # 匿名聊天
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] {(Event.current and "开启了匿名聊天")or "关闭了匿名聊天"}'))
            elif Event.type == 'GroupAllowConfessTalkEvent': # 坦白说
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] {(Event.current and "开启了坦白说")or "关闭了坦白说"}'))
            elif Event.type == 'GroupAllowMemberInviteEvent': # 允许群员邀请好友加群
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.group.name}({Event.group.id}) {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] {(Event.current and "开启了邀请入群")or "关闭了邀请入群"}'))
            elif Event.type == 'MemberJoinEvent': # 新人入群的事件
                bot.SendMsg('Friend',f,soup.Text(f'新人 {Event.member.memberName}({Event.member.id}) 加入了 {Event.member.group.name}({Event.member.group.id}) 群'))
                words = [
                    [soup.Text('欢迎新人'),soup.Face(13)],
                ]
                if first:bot.SendMsg('Group',Event.member.group.id,*words[random.randint(0,len(words)-1)])
            elif Event.type == 'MemberLeaveEventKick': # 成员被踢出群（该成员不是Bot）
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.operator.group.name}({Event.operator.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 踢了'))
                if first:bot.SendMsg('Group',Event.member.group.id,soup.Face(13))
            elif Event.type == 'MemberLeaveEventQuit': # 成员主动离群（该成员不是Bot）
                bot.SendMsg('Friend',f,soup.Text(f'{Event.member.memberName}({Event.member.id}) 退出了 {Event.member.group.name}({Event.member.group.id})'))
            elif Event.type == 'MemberCardChangeEvent': # 群名片改动
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.origin}({Event.member.id}) 改名为 {Event.current}'))
            elif Event.type == 'MemberSpecialTitleChangeEvent': # 群头衔改动（只有群主有操作限权）
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 头衔 {Event.origin} 改为 {Event.current}'))
            elif Event.type == 'MemberPermissionChangeEvent': # 成员权限改变的事件（该成员不是Bot）
                bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 权限 {Event.origin} 改为 {Event.current}'))
            elif Event.type == 'MemberMuteEvent': # 群成员被禁言事件（该成员不是Bot）
                if Event.operator:bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 禁言 {time.strftime(f"{time.gmtime(Event.durationSeconds)[2]-1} %H:%M",time.gmtime(Event.durationSeconds))}'))
                else:bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 被禁言 {time.strftime(f"{time.gmtime(Event.durationSeconds)[2]-1} %H:%M",time.gmtime(Event.durationSeconds))}'))
                if first:bot.SendMsg('Group',Event.member.group.id,soup.At(Event.member.id),soup.Text('你倒是说句话呀'),soup.Face(13))
            elif Event.type == 'MemberUnmuteEvent': # 群成员被取消禁言事件（该成员不是Bot）
                if Event.operator:bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 被 {Event.operator.memberName}[{Event.operator.permission}({Event.operator.id})] 解禁'))
                else:bot.SendMsg('Friend',f,soup.Text(f'群 {Event.member.group.name}({Event.member.group.id}) 成员 {Event.member.memberName}({Event.member.id}) 被解除禁言'))
                if first:bot.SendMsg('Group',Event.member.group.id,soup.Text('啧'))
            elif Event.type == 'MemberHonorChangeEvent': # 群员称号改变
                bot.SendMsg('Friend',f,soup.Text(f'成员 {Event.member.memberName}({Event.member.id}) 在群 {Event.member.group.name}({Event.member.group.id}) {(Event.action=="achieve"and"获得")or "失去"} {Event.honor} 称号'))
                if first and Event.action=='achieve' and Event.honor=='龙王' and Event.member.id!=bot.conf.qq:bot.SendMsg('Group',Event.member.group.id,soup.At(Event.member.id),soup.Text('龙王给爷喷水'))
            elif Event.type == 'OtherClientOnlineEvent': # 其他客户端上线
                bot.SendMsg('Friend',f,soup.Text(f'{Event.client.platform} 客户端{(hasattr(Event,"kind") and Event.kind)or""}上线'))
            elif Event.type == 'OtherClientOfflineEvent': # 其他客户端下线
                bot.SendMsg('Friend',f,soup.Text(f'{Event.client.platform} 客户端下线'))
            elif Event.type == 'CommandExecutedEvent': # 命令被执行
                pass
            else:raise
        except:
            bot.SendMsg('Friend',f,soup.Text(trans(Event)))
            bot.SendMsg('Friend',f,soup.Text(traceback.format_exc()))
        first = False

def onQQRequestEvent(bot, Request):
    '''\
    申请事件'''
    for f in admin_ID():
        print(Request)
        if Request.request_type == 'friend':bot.SendMsg('Friend',f.user_id,soup.Text(f'来自 {Request.user_id} 的好友申请，事件标识：{Request.flag}'))
        else:bot.SendMsg('Friend',f.user_id,soup.Text(f'来自 {Request.user_id} 的{"申请" if Request.sub_type else "邀请"}，{"申请" if Request.sub_type else "邀请"}加入{Request.group_id}，事件标识：{Request.flag}'))
    if Request.request_type == 'friend':
        return True, None # 同意，别名
    elif Request.sub_type == 'add':
        return True, None # 同意，拒绝原因
    else:
        return True, None # 同意，拒绝原因