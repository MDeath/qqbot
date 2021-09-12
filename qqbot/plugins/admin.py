# -*- coding: utf-8 -*-

import os
import __soup as soup


def onUnplug(bot):
    '此插件不可卸载'
    bot.Plug(str(__name__))

def admin_ID(bot, ID, admin=False):
    for f in bot.Friend:
        if f.id == ID and f.remark == 'Admin':return True
        elif f.id == ID and f.remark == 'User' and admin == 0:return True
    else:return False


def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
@bot 并输入指令使用
菜单
重启
更新联系人
插件列表
加载插件《插件名》
卸载插件《插件名》
说明(可附带插件名)\
    '''
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
        if bot.conf.qq not in At:
            return
    else:
        target = Sender.id

    n = '\n'
    plug = [m.split('.')[0] for m in os.listdir(bot.conf.pluginPath)]
    
    if 'who is your daddy' == Plain:
            bot.SendMessage(Type, target, message=[soup.At(Sender.id)])

    elif '菜单' in Plain:
        bot.SendMessage(Type, target, message=[soup.Plain(onQQMessage.__doc__)])

    elif '说明' in Plain:
        moduleName = Plain.replace('说明','').replace(' ','')
        if moduleName != '' and moduleName in bot.Plugins():
            module = bot.plugins[moduleName]
            for slotName in bot.slotsTable.keys():
                if hasattr(module, slotName):
                    mod = getattr(module,slotName)
                    Plain += f'{n}{mod.__name__}{(mod.__doc__ and n+mod.__doc__) or ""}'
        elif moduleName == '':
            Plain = '已加载模块说明'
            for moduleName in bot.plugins.keys():
                module = bot.plugins[moduleName]
                Plain += '\n' + moduleName + '模块'
                for slotName in bot.slotsTable.keys():
                    if hasattr(module, slotName):
                        mod = getattr(module,slotName)
                        Plain += f'{n}{mod.__name__}{(mod.__doc__ and n+mod.__doc__) or ""}'
        bot.SendMessage(Type, target, message=[soup.Plain(Plain)])

    elif '插件列表' == Plain.replace(' ',''):
        for p in plug:
            if '__' in p:
                continue
            elif p in bot.Plugins():
                Plain += f'\n已加载 {p}'
            else:
                Plain += f'\n未加载 {p}'
        message = [soup.Plain(Plain)]
        bot.SendMessage(Type, target, message=message)

    if admin_ID(bot, Sender.id, True):
        if '重启' == Plain:
            bot.SendMessage(Type, target, [soup.Plain('正在重启')])
            bot.Restart()

    if admin_ID(bot, Sender.id):
        if '更新联系人' == Plain:
            bot.Update()
            bot.SendMessage(Type, target, [soup.Plain('更新完毕')])

        elif '加载插件' in Plain:
            moduleName = Plain.replace('加载插件','')
            Modules = moduleName.split(' ')
            for m in Modules:
                if f'{m}.py' in plug or m in plug:
                    bot.Plug(m)
                    if m in bot.Plugins():
                        bot.SendMessage(Type, target, message=[soup.Plain(f'成功加载 {m}')])
                    else:
                        bot.SendMessage(Type, target, message=[soup.Plain(f'{m} 加载失败')])
                elif m != '':
                    bot.SendMessage(Type, target, message=[soup.Plain(f'库中没有 {m}')])
        if '卸载插件' in Plain:
            moduleName = Plain.replace('卸载插件','')
            Modules = moduleName.split(' ')
            for m in Modules:
                if m in bot.Plugins():
                    bot.Unplug(m)
                    if m in bot.Plugins():
                        bot.SendMessage(Type, target, message=[soup.Plain(f'{m} 卸载失败')])
                    else:
                        bot.SendMessage(Type, target, message=[soup.Plain(f'成功卸载 {m}')])
                elif m != '':
                    bot.SendMessage(Type, target, message=[soup.Plain(f'{m} 没有加载')])


def onQQEvent(bot, Message):
    '申请事件'
    if Message.type == 'MemberJoinRequestEvent':
        return 0, '欢迎'
    elif Message.type == 'NewFriendRequestEvent':
        return 0, 'hello'
    elif Message.type == 'BotInvitedJoinGroupRequestEvent':
        return 0, '大家好我是 robot'
    else: return None, ''
