# -*- coding: utf-8 -*-

import os,json,time,traceback

from qqbotcls import QQBotSched
from mainloop import Put
import soup

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
    bot.heart = time.strftime("%Y-%m-%d\n%H:%M:%S\n%z\n%a-%A\n%b-%B\n%c\n%I %p",time.localtime())

def onUnplug(bot):
    '''\
    此插件不可卸载'''
    bot.Plug(__name__)

def admin_ID(bot, ID, admin=False):
    for f in bot.Friend:
        if f.id == ID and f.remark == 'Admin':return True
        elif f.id == ID and f.remark == 'User' and admin == 0:return True
    else:return False

def Reply(bot,type,target):
    def func(*message,quote=None):
        return bot.SendMessage(type,target,*message,quote=quote)
    return func

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    输入指令使用
    ### 一般权限
    菜单
    更新联系人
    插件列表
    说明(可附带插件名)
    ### 管理员权限
    加载插件《插件名》
    卸载插件《插件名》
    ### 超级权限
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
        if msg.type == 'FlashImage':FlashImage.append(msg)
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
    reply = Reply(bot,Type,target)
    if Plain.startswith(('$', '￥'))and admin_ID(bot ,Sender.id, True):
        try:
            rt = eval(Plain[1:])
        except:
            rt = traceback.format_exc()
        reply(soup.Plain(rt))
        return
    
    n = '\n'
    plug = [m.split('.')[0] for m in os.listdir(bot.conf.pluginPath)]
    
    if bot.conf.qq in At and Plain in ['who is your daddy','你是谁的']:
        reply(soup.At(Sender.id))
        return

    elif '菜单' == Plain:
        reply(soup.Plain(onQQMessage.__doc__))
        return

    elif Plain.startswith('说明'):
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
            message += '\n' + module.__name__ + '模块'
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

    if admin_ID(bot, Sender.id):
        if '更新联系人' == Plain:
            bot.Update()
            reply(soup.Plain('更新完毕'))
            return

        elif Plain.startswith('加载插件'):
            moduleName = Plain.replace('加载插件','')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m:
                    result = bot.Plug(m)
                    reply(soup.Plain(result))
            return

        if Plain.startswith('卸载插件'):
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
            bot.SendMessage(Type, target, soup.Plain(message), quote=quote)

    if admin_ID(bot, Sender.id, True):
        if '重启' == Plain:
            reply(soup.Plain('bot正在重启'))
            Put(bot.Restart)
            return

        elif '关机' == Plain:
            reply(soup.Plain('bot以关闭'))
            Put(bot.Stop)

def onQQEvent(bot, Message):pass

def onQQRequestEvent(bot, Message):
    '''\
    申请事件'''
    if Message.type == 'MemberJoinRequestEvent':
        '''
        0	同意入群
        1	拒绝入群
        2	忽略请求
        3	拒绝入群并添加黑名单，不再接收该用户的入群申请
        4	忽略入群并添加黑名单，不再接收该用户的入群申请'''
        return 0, '欢迎'
    elif Message.type == 'NewFriendRequestEvent':
        '''
        0	同意添加好友
        1	拒绝添加好友
        2	拒绝添加好友并添加黑名单，不再接收该用户的好友申请'''
        return 0, '发送 菜单 查看基本指令'
    elif Message.type == 'BotInvitedJoinGroupRequestEvent':
        '''
        0	同意邀请
        1	拒绝邀请'''
        return 0, '发送 菜单 查看基本指令'
    else: return None, ''