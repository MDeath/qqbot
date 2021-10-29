# -*- coding: utf-8 -*-

import os,json
import traceback
from mainloop import Put
import soup


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
    @bot 并输入指令使用
    菜单
    重启
    更新联系人
    插件列表
    加载插件《插件名》
    卸载插件《插件名》
    说明(可附带插件名)'''
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
    
    if 'who is your daddy' == Plain and admin_ID(bot ,Sender.id, True):
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

        elif '休眠' == Plain:
            for p in bot.Plugins():
                bot.Unplug(p)
            reply(soup.Plain('bot已休眠'))
            return

        elif '喂' == Plain:
            for p in bot.conf.plugins:
                bot.Plug(p)
            reply(soup.Plain('bot已唤醒'))
            return
        
def onQQEvent(bot, Message):
    '''\
    申请事件'''
    if Message.type == 'MemberJoinRequestEvent':
        return 0, '欢迎'
    elif Message.type == 'NewFriendRequestEvent':
        return 0, 'hello'
    elif Message.type == 'BotInvitedJoinGroupRequestEvent':
        return 0, '大家好我是 robot'
    else: return None, ''