# -*- coding: utf-8 -*-

import os,json,psutil,random,time,traceback

from qqbotcls import QQBotSched,_bot
from mainloop import Put
import soup

@property
def battery():return f'{psutil.sensors_battery().percent}%'
    
def admin_ID(user=False):
    return [f.id for f in _bot.Friend if(f.remark=='Admin'and f.nickname!='Admin')or(f.remark=='User'and f.nickname!='User'and user)]

def trans(s:str):
    for k,v in [
        ['friend','好友'],
        ['group','群组'],
        ['temp','临时聊天'],
        ['message','消息'],
        ['event','事件'],
        ['request','请求'],
        ['join','加入'],
        ['invited','邀请'],
        ['invite','邀请'],
        ['member','成员'],
        ['recall','撤回'],
        ['input','输入'],
        ['status','状态'],
        ['changed','改变'],
        ['change','改变'],
        ['bot','机器人'],
        ['offline','离线'],
        ['online','上线'],
        ['oropped','移除'],
        ['relogin','重新登录'],
        ['active','主动'],
        ['force','强制'],
        ['nick','昵称'],
        ['permission','权限'],
        ['mute','禁言'],
        ['unmute','禁言解除'],
        ['leave','退群'],
        ['kick','踢出'],
        ['nudge','戳一戳'],
        ['name','名字'],
        ['entrance','入群'],
        ['announcement','公告'],
        ['muteall','全体禁言'],
        ['allow','允许'],
        ['anonymouschat','匿名聊天'],
        ['confessTalk','坦白说'],
        ['quit','退出'],
        ['card','名片'],
        ['specialTitle','群头衔'],
        ['honor','称号'],
        ['new','新的'],
        ['other','其他'],
        ['client','客户端'],
        ['commandExecuted','命令行执行'],
        ['',''],
    ]:
        s = str(s).lower().replace(k,v)
    return s

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=None, 
            minute=None, 
            second=0, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def heartbeat(bot):
    '定时任务心跳'
    bot.heart = time.strftime("HeartBeat\n%Y-%m-%d\n%H:%M:%S\n%z\n%a-%A\n%b-%B\n%c\n%I %p",time.localtime())

def onPlug(bot):
    bot.battery = psutil.sensors_battery().percent

def onUnplug(bot):
    '''\
    此插件不可卸载'''
    bot.Plug(__name__)

def onInterval(bot):
    battery = psutil.sensors_battery().percent
    if bot.battery != battery:
        for f in admin_ID():
            if 100 > battery > bot.battery >= 90:
                bot.SendMessage('Friend',f,soup.Plain(f'电池电量已到达 {battery} %，请停止充电'))
            elif 20 > bot.battery > battery > 0:
                bot.SendMessage('Friend',f,soup.Plain(f'电池电量已不足 {battery} %，请接上电源'))
            elif battery == 0:
                bot.SendMessage('Friend',f,soup.Plain(f'电池电量已不足 {battery} %，即将要关机'))
            elif battery - bot.battery > 5 or bot.battery - battery > 5:
                bot.SendMessage('Friend',f,soup.Plain(f'电池电量{battery} %'))
        bot.battery = battery

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    输入指令使用
    -=# 一般权限 #=-
    菜单
    更新联系人
    插件列表
    说明(可附带插件名)
    -=# 管理员权限 #=-
    加载插件《插件名》
    卸载插件《插件名》
    -=# 超级权限 #=-
    关机 重启 
    命令行前置符 ￥ 或 $'''
    if Type not in ['Friend', 'Group']:
        return
    At = []
    AtAll = False
    Plain = ''
    Image = []
    FlashImage = []
    Json = []
    for msg in Message:
        if msg.type == 'Quote':Quote = msg
        if msg.type == 'At':At.append(msg.target)
        if msg.type == 'AtAll':AtAll = True
        if msg.type == 'Face':pass
        if msg.type == 'Plain':Plain += msg.text
        if msg.type == 'Image':Image.append(msg)
        if msg.type == 'FlashImage':FlashImage = msg
        if msg.type == 'Voice':Voice = msg
        if msg.type == 'Xml':Xml = msg.xml
        if msg.type == 'Json':Json.append(msg.json)
        if msg.type == 'App':App = msg.content
        if msg.type == 'Poke':pass 
        if msg.type == 'Dice':pass
        if msg.type == 'MusicShare':MusicShare = msg
        if msg.type == 'ForwardMessage':pass 
        if msg.type == 'File':pass

    if hasattr(Sender, 'group'):
        target = Sender.group.id
    else:
        target = Sender.id

    reply = lambda *msg:bot.SendMessage(Type,target,*msg)

    if Plain.startswith(('$', '￥'))and Sender.id in admin_ID(True):
        try:
            rt = eval(Plain[1:])
        except:
            rt = traceback.format_exc()
        reply(soup.Plain(rt))
        return
    
    if FlashImage:
        msg = f"{(hasattr(Sender,'group')and'群 '+Sender.group.name+'('+str(Sender.group.id)+') '+Sender.memberName+'('+str(Sender.id)+') ')or'好友 '+Sender.nickname+'('+str(Sender.id)+') '} 的闪图"
        [bot.SendMessage('Friend',a,soup.Plain(msg),soup.Image(id=FlashImage.imageId))for a in admin_ID()]
    if bot.conf.qq in At:[bot.SendMessage('Friend',a,soup.Plain(f"[@ME] in 群 {Sender.group.name}({Sender.group.id}) {Sender.memberName}({Sender.id}):\n"),*[msg if msg.type!='At' else soup.Plain(f"{(msg.target==bot.conf.qq and '[@ME]')or f'@{msg.target}'}") for msg in Message])for a in admin_ID()]

    n = '\n'
    plug = [m.split('.')[0] for m in os.listdir(bot.conf.pluginPath)]
    
    if Plain.strip() in ['菜单','帮助','help','memu']:
        reply(soup.Plain(onQQMessage.__doc__))
        return

    elif Plain.strip().startswith('说明'):
        moduleName = Plain.replace('说明','',1).replace(' ','')
        if moduleName != '' and moduleName in bot.Plugins():
            message = Plain
            modules = [bot.plugins[moduleName]]
        elif moduleName == '':
            message = '已加载模块说明'
            modules = [bot.plugins[moduleName] for moduleName in bot.plugins.keys()]
        else:
            return
        for module in modules:
            message += '\n-=# ' + module.__name__ + '模块 #=-'
            for slotName in bot.slotsTable.keys():
                if hasattr(module, slotName):
                    mod = getattr(module,slotName)
                    if mod.__doc__:
                        message += n+mod.__name__+n+mod.__doc__+n
        return reply(soup.Plain(message))

    elif '插件列表' == Plain:
        for p in plug:
            if '__' in p:
                continue
            elif p in bot.Plugins():
                Plain += f'\n已加载 {p}'
            else:
                Plain += f'\n未加载 {p}'
        reply(soup.Plain(Plain))
        return

    if '更新联系人' == Plain:
        bot.Update()
        reply(soup.Plain('更新完毕'))
        return

    if Sender.id in admin_ID(True):
        if Plain.strip().startswith('加载插件'):
            moduleName = Plain.replace('加载插件','')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m:
                    result = bot.Plug(m)
                    reply(soup.Plain(result))
            return

        if Plain.strip().startswith('卸载插件'):
            moduleName = Plain.replace('卸载插件','')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m:
                    result = bot.Unplug(m)
                    reply(soup.Plain(result))
            return
        if Plain == '解析'and Quote:
            quote = Quote.id
            Quote = bot.MessageFromId(Quote.id)
            message = json.dumps(Quote.messageChain, ensure_ascii=False, indent=4)
            message = message.replace('\\\\', '\\')
            message = message.replace('\\\'','\'')
            message = message.replace('\\\"','\"')
            bot.SendMessage(Type, target, soup.Plain(message), id=quote)

    if Sender.id in admin_ID():
        if '重启' == Plain:
            reply(soup.Plain('bot正在重启'))
            Put(bot.Restart)
            return

        elif '关机' == Plain:
            reply(soup.Plain('bot以关闭'))
            Put(bot.Stop)

def onQQEvent(bot, Message):
    '''\
    事件处理'''
    first = True
    for f in admin_ID():
        try:
            if Message.type == 'BotOnlineEvent': # Bot登录成功
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.qq} 登陆成功'))
            elif Message.type == 'BotOfflineEventActive': # Bot主动离线
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.qq} 主动离线'))
            elif Message.type == 'BotOfflineEventForce': # Bot被挤下线
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.qq} 被挤下线'))
            elif Message.type == 'BotOfflineEventDropped': # Bot被服务器断开或因网络问题而掉线
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.qq} 被服务器断开或因网络问题而掉线'))
            elif Message.type == 'BotReloginEvent': # Bot主动重新登录
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.qq} 主动重新登录'))
            elif Message.type == 'FriendInputStatusChangedEvent': # 好友输入状态改变
                pass # bot.SendMessage('Friend',f,soup.Plain(f'好友 {Message.friend.nickname}[{Message.friend.remark}({Message.friend.id})] {((Message.inputting and "正在输入") or "取消输入")}'))
            elif Message.type == 'FriendNickChangedEvent': # 好友昵称改变
                bot.SendMessage('Friend',f,soup.Plain(f'好友 {Message.friend.nickname}[{Message.friend.remark}({Message.friend.id})] 昵称改为 {Message.to}'))
            elif Message.type == 'BotGroupPermissionChangeEvent': # Bot在群里的权限被改变. 操作人一定是群主
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) 权限由 {Message.origin} 改为 {Message.current}'))
            elif Message.type == 'BotMuteEvent': # Bot被禁言
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.operator.group.name}({Message.operator.group.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 禁言 {time.strftime("%j天%H时%M分",time.gmtime(Message.durationSeconds))}'))
            elif Message.type == 'BotUnmuteEvent': # Bot被取消禁言
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.operator.group.name}({Message.operator.group.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 解禁'))
            elif Message.type == 'BotJoinGroupEvent': # Bot加入了一个新群
                bot.SendMessage('Friend',f,soup.Plain(f'加入 {Message.group.name}({Message.group.id}) 群'))
            elif Message.type == 'BotLeaveEventActive': # Bot主动退出一个群
                bot.SendMessage('Friend',f,soup.Plain(f'退出 {Message.group.name}({Message.group.id}) 群'))
            elif Message.type == 'BotLeaveEventKick': # Bot被踢出一个群
                bot.SendMessage('Friend',f,soup.Plain(f'被踢出 {Message.group.name}({Message.group.id}) 群'))
            elif Message.type == 'BotLeaveEventDisband': # Bot因群主解散群而退出群, 操作人一定是群主
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) 被解散'))
            elif Message.type == 'GroupRecallEvent': # 群消息撤回
                bot.SendMessage('Friend',f,soup.Forward(soup.Node(id=Message.messageId)))
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 撤回了 {Message.authorId} 的消息ID {Message.messageId}'))
            elif Message.type == 'FriendRecallEvent': # 好友消息撤回
                bot.SendMessage('Friend',f,soup.Forward(soup.Node(id=Message.messageId)))
                bot.SendMessage('Friend',f,soup.Plain(f'好友 {Message.authorId} 撤回了消息ID {Message.messageId}'))
            elif Message.type == 'NudgeEvent': # 戳一戳事件
                if Message.target==bot.conf.qq:bot.SendMessage('Friend',f,soup.Plain(f'{(Message.subject.kind=="Group" and "群") or "好友"}({Message.fromId}) 戳了戳 {Message.target} 的脸'))
            elif Message.type == 'GroupNameChangeEvent': # 某个群名改变
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.origin}({Message.group.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 改成 {Message.current}'))
            elif Message.type == 'GroupEntranceAnnouncementChangeEvent': # 某群入群公告改变
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) 公告:\n{Message.origin}\n被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 改为:\n{Message.current}'))
            elif Message.type == 'GroupMuteAllEvent': # 全员禁言
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] {(Message.current and "开启了全员禁言")or "关闭了全员禁言"}'))
            elif Message.type == 'GroupAllowAnonymousChatEvent': # 匿名聊天
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] {(Message.current and "开启了匿名聊天")or "关闭了匿名聊天"}'))
            elif Message.type == 'GroupAllowConfessTalkEvent': # 坦白说
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] {(Message.current and "开启了坦白说")or "关闭了坦白说"}'))
            elif Message.type == 'GroupAllowMemberInviteEvent': # 允许群员邀请好友加群
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.group.name}({Message.group.id}) {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] {(Message.current and "开启了邀请入群")or "关闭了邀请入群"}'))
            elif Message.type == 'MemberJoinEvent': # 新人入群的事件
                bot.SendMessage('Friend',f,soup.Plain(f'新人 {Message.member.memberName}({Message.member.id}) 加入了 {Message.member.group.name}({Message.member.group.id}) 群'))
                if first:bot.SendMessage('Group',Message.member.group.id,soup.Plain('欢迎新人'),soup.Face(13))
            elif Message.type == 'MemberLeaveEventKick': # 成员被踢出群（该成员不是Bot）
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.operator.group.name}({Message.operator.group.id}) 成员 {Message.member.memberName}({Message.member.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 踢了'))
                if first:bot.SendMessage('Group',Message.member.group.id,soup.Face(13))
            elif Message.type == 'MemberLeaveEventQuit': # 成员主动离群（该成员不是Bot）
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.member.memberName}({Message.member.id}) 退出了 {Message.member.group.name}({Message.member.group.id})'))
            elif Message.type == 'MemberCardChangeEvent': # 群名片改动
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.member.group.name}({Message.member.group.id}) 成员 {Message.origin}({Message.member.id}) 改名为 {Message.current}'))
            elif Message.type == 'MemberSpecialTitleChangeEvent': # 群头衔改动（只有群主有操作限权）
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.member.group.name}({Message.member.group.id}) 成员 {Message.member.memberName}({Message.member.id}) 头衔 {Message.origin} 改为 {Message.current}'))
            elif Message.type == 'MemberPermissionChangeEvent': # 成员权限改变的事件（该成员不是Bot）
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.member.group.name}({Message.member.group.id}) 成员 {Message.member.memberName}({Message.member.id}) 权限 {Message.origin} 改为 {Message.current}'))
            elif Message.type == 'MemberMuteEvent': # 群成员被禁言事件（该成员不是Bot）
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.operator.group.name}({Message.operator.group.id}) 成员 {Message.member.memberName}({Message.member.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 禁言 {time.strftime("%j天%H时%M分",time.gmtime(Message.durationSeconds))}'))
                if first:bot.SendMessage('Group',Message.member.group.id,soup.At(Message.member.id),soup.Plain('你倒是说句话呀'),soup.Face(13))
            elif Message.type == 'MemberUnmuteEvent': # 群成员被取消禁言事件（该成员不是Bot）
                bot.SendMessage('Friend',f,soup.Plain(f'群 {Message.operator.group.name}({Message.operator.group.id}) 成员 {Message.member.memberName}({Message.member.id}) 被 {Message.operator.memberName}[{Message.operator.permission}({Message.operator.id})] 解禁'))
                if first:bot.SendMessage('Group',Message.member.group.id,soup.Plain('啧'))
            elif Message.type == 'MemberHonorChangeEvent': # 群员称号改变
                bot.SendMessage('Friend',f,soup.Plain(f'成员 {Message.member.memberName}({Message.member.id}) 在群 {Message.member.group.name}({Message.member.group.id}) {(Message.action=="achieve"and"获得")or "失去"} {Message.honor} 称号'))
                if first and Message.action=='achieve' and Message.honor=='龙王':bot.SendMessage('Group',Message.member.group.id,soup.At(Message.member.id),soup.Plain('龙王给爷喷水'))
            elif Message.type == 'OtherClientOnlineEvent': # 其他客户端上线
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.client.platform} 客户端{(hasattr(Message,"kind") and Message.kind)or""}上线'))
            elif Message.type == 'OtherClientOfflineEvent': # 其他客户端下线
                bot.SendMessage('Friend',f,soup.Plain(f'{Message.client.platform} 客户端下线'))
            elif Message.type == 'CommandExecutedEvent': # 命令被执行
                pass
            else:
                print(Message)
                bot.SendMessage('Friend',f,soup.Plain(trans(Message)))
        except:
            bot.SendMessage('Friend',f,soup.Plain(trans(Message)))
            bot.SendMessage('Friend',f,soup.Plain(traceback.format_exc()))
        first = False

def onQQRequestEvent(bot, Message):
    '''\
    申请事件'''
    for f in admin_ID():
        if Message.type == 'NewFriendRequestEvent': # 添加好友申请
            '''
            0	同意添加好友
            1	拒绝添加好友
            2	拒绝添加好友并添加黑名单，不再接收该用户的好友申请'''
            bot.SendMessage('Friend',f,soup.Plain(f'{Message.nick}({Message.fromId}){(Message.groupId and" 通过群 "+[g.name for g in bot.Group if g.id==Message.groupId][0]+"("+str(Message.groupId)+")")or ""} 申请好友'))
            return 0, '发送 菜单 查看基本指令'
        elif Message.type == 'MemberJoinRequestEvent': # 用户入群申请（Bot需要有管理员权限）
            '''
            0	同意入群
            1	拒绝入群
            2	忽略请求
            3	拒绝入群并添加黑名单，不再接收该用户的入群申请
            4	忽略入群并添加黑名单，不再接收该用户的入群申请'''
            bot.SendMessage('Friend',f,soup.Plain(f'{Message.nick}({Message.fromId}) 申请加入 {[g.name for g in bot.Group if g.id==Message.groupId][0]}({Message.groupId})'))
            return 0, '欢迎'
        elif Message.type == 'BotInvitedJoinGroupRequestEvent': # Bot被邀请入群申请
            '''
            0	同意邀请
            1	拒绝邀请'''
            bot.SendMessage('Friend',f,soup.Plain(f'{Message.nick}({Message.fromId}) 邀请加入 {Message.groupId} 群'))
            return 0, '发送 菜单 查看基本指令'
        else:
            bot.SendMessage('Friend',f,soup.Plain(trans(Message)))
            return None, ''