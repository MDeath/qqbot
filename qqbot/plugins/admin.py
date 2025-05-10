# -*- coding: utf-8 -*-

import os,json,psutil,random,time,traceback

from qqbotcls import QQBotSched,bot
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING, SetLogLevel, EnableLog, DisableLog
from mainloop import Put, PutBack
from common import JsonDict, DotDict, secs2hours, B2B, b64dec, b64enc, jsondumps, jsonloads, SGR
import soup

def admin_ID(user=False,me=False) -> list:
    return [f for f in bot.Friend() if f.remark=='Admin' or (user and f.remark=='User') or (me and f.user_id==bot.qq)]

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

@QQBotSched(year=None,
            month=None,
            day=None,
            week=None,
            day_of_week=None,
            hour=None,
            minute=','.join(map(str,range(0,60,5))),
            second=30,
            start_date=None,
            end_date=None,
            timezone=None)
def Chime(bot):
    '定时任务'
    if random.randint(0,1):DEBUG(soup.Text(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())))
    else:DEBUG(soup.Text(time.strftime('%Y%m%d %H%M%S',time.localtime())))

def onPlug(bot):
    bot.battery = psutil.sensors_battery()
    bot.battery = bot.battery.percent if bot.battery else None

def onUnplug(bot):
    '''\
    此插件不可卸载'''
    bot.Plug(__name__)

def onInterval(bot):pass

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
            for keyword in ['日志等级', 'setloglevel']:Text = Text.replace(keyword,'').strip()
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
        group = bot.Group(group_id=Notice.group_id)[0]
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
        return

    if Notice.notice_type == 'group_increase': # 群成员增加
        {'time': 1737431992, 'self_id': 2907237958, 'post_type': 'notice', 'notice_type': 'group_increase', 'sub_type': 'approve', 'group_id': 683327278, 'operator_id': 183744529, 'operator_uid': 'u_mEg0pkdNJZBsh5PmiJtZBw', 'user_id': 2117636781, 'user_uid': 'u_Hd9dRGd0SK2L0lS-5rUX_Q', 'sender_id': 183744529, 'target_id': 2117636781, 'target_uid': 'u_Hd9dRGd0SK2L0lS-5rUX_Q', 'source': 'group'}
        bot.SendMsg('group',Notice.group_id,soup.Text('欢迎新人'),soup.Face(13),soup.At(Notice.user_id))
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        group = bot.Group(group_id=Notice.group_id)[0]
        for f in admin_ID():
            bot.SendMsg('friend',f.user_id,soup.Text(f'{member.nickname}({member.user_id}) 加入了 {group.group_name}({group.group_id})'))
        return

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
            bot.SendMsg('group',Notice.group_id,soup.Text('啧'))
            for f in admin_ID():bot.SendMsg('Friend',f.user_id,soup.Text(f'群 {group.group_name}({group.group_id}) 成员 {member.nickname}({member.user_id}) 被 {user.nickname}[{user.role}({user.user_id})] 解除禁言'))
        return
    
    if Notice.notice_type == 'group_recall': # 群消息撤回
        group = bot.Group(group_id=Notice.group_id)[0]
        user = bot.Member(group_id=Notice.group_id,user_id=Notice.operator_id)[0]
        member = bot.Member(group_id=Notice.group_id,user_id=Notice.user_id)[0]
        for f in admin_ID():
            message = bot.GetMsg(Notice.message_id)
            bot.SendMsg('friend', f.user_id, soup.Node(*message.message,uid=message.sender.user_id,nickname=message.sender.nickname))
            bot.SendMsg('friend', f.user_id, soup.Text(f'群 {group.group_name}({group.group_id}) {user.nickname}[{user.role}({user.user_id})] 撤回了 {"" if user.user_id==member.user_id else f" {member.nickname}[{member.role}({member.user_id})] 的"}消息ID {Notice.message_id}'))
        return
    
    if Notice.notice_type == 'group_card': # 群成员名片变动
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

    if Notice.notice_type == 'reaction': # 群消息反应
        # time          | int | -               | 事件发生的时间戳
        # self_id       | int | -               | 收到事件的机器人 QQ 号
        # post_type     | str | `notice`        | 上报类型
        # notice_type   | str | `reaction`      | 消息类型
        # sub_type      | str | `add`、`remove` | 提示类型
        # group_id      | int | -               | 群号
        # message_id    | int | -               | 反应的消息 ID
        # operator_id   | int | -               | 操作者 QQ 号
        # code          | str | -               | 表情 ID
        # count         | int | -               | 当前反应数量
        return

    if Notice.notice_type == 'friend_add': # 好友添加
        pass
    if Notice.notice_type == 'friend_recall': # 好友消息撤回
        friend = bot.Friend(user_id=Notice.user_id)[0]
        for f in admin_ID():
            message = bot.GetMsg(Notice.message_id)
            bot.SendMsg('friend', f.user_id, soup.Node(*message.message,uid=friend.user_id,nickname=friend.nickname))
            bot.SendMsg('friend', f.user_id, soup.Text(f'好友{friend.nickname}[{friend.remark}({friend.user_id})]撤回了消息 {Notice.message_id}'))
        return
    if Notice.notice_type == 'offline_file': # 接收到离线文件包
        pass
    if Notice.notice_type == 'client_status': # 客户端状态
        pass
    for f in admin_ID():bot.SendMsg('friend', f.user_id,soup.Text(Notice))
    return
    
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