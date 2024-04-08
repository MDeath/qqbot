# -*- coding: utf-8 -*-

import os, sys, time, subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from collections import defaultdict

from mainloop import MainLoop, Put
from miraiapi import MiraiApi, RequestError
from common import DotDict, Import, JsonDict, StartDaemonThread, SGR
from qconf import QConf
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from qterm import QTermServer
from termbot import TermBot

RESTART = 201

def _call(func, *args, **kwargs):
    try:
        StartDaemonThread(func, *args, **kwargs)
    except Exception as e:
        ERROR('', exc_info=True)
        ERROR('执行 %s.%s 时出错，%s', func.__module__, func.__name__, e)

class QQBot(TermBot):
    def __init__(self) -> None:
        self.scheduler = BackgroundScheduler(daemon=True)
        self.schedTable = defaultdict(list)
        self.slotsTable = {
            'onStartupComplete':[],
            'onInterval':[],
            'onQQMessage':[],
            'onQQEvent':[],
            'onPlug':[],
            'onUnplug':[],
            'onExit':[]
        }
        self.plugins = JsonDict()

    def Init(self, argv=[]):
        for name, slots in self.slotsTable.items():
            setattr(self, name, self.wrap(slots))
        self.slotsTable['onQQRequestEvent'] = []
        self.conf = QConf(argv)
        self.conf.Display()

        self.Mirai = MiraiApi(self.conf.qq, self.conf.verifyKey, self.conf.host, self.conf.port)
        while not self.Mirai.started:pass

        self.MessageId = self.Mirai.MessageId
        self.SendMessage = self.Mirai.SendMessage
        self.Nudge = self.Mirai.Nudge
        self.Recall = self.Mirai.Recall
        self.Roaming = self.Mirai.Roaming
        self.List = self.Mirai.List
        self.Profile = self.Mirai.Profile
        self.DelFriend = self.Mirai.DelFriend
        self.Mute = self.Mirai.Mute
        self.Kick = self.Mirai.Kick
        self.Quit = self.Mirai.Quit
        self.MuteAll = self.Mirai.MuteAll
        self.SetEssence = self.Mirai.SetEssence
        self.GroupConfig = self.Mirai.GroupConfig
        self.MemberInfo = self.Mirai.MemberInfo
        self.MemberAdmin = self.Mirai.MemberAdmin
        self.AnnoList = self.Mirai.AnnoList
        self.AnnoPut = self.Mirai.AnnoPut
        self.AnnoDel = self.Mirai.AnnoDel
        self.FileList = self.Mirai.FileList
        self.FileInfo = self.Mirai.FileInfo
        self.FileMkdir = self.Mirai.FileMkdir
        self.FileDel = self.Mirai.FileDel
        self.FileMove = self.Mirai.FileMove
        self.FilereName = self.Mirai.FilereName
        self.FileUpload = self.Mirai.FileUpload
        self.Upload = self.Mirai.Upload

    def Run(self):
        for pluginName in self.conf.plugins:
            self.Plug(pluginName)

        self.onStartupComplete()
        self.onPlug()

        # child thread 1
        StartDaemonThread(self.Mirai.pollForever, self.MessageAnalyst)
        # child thread 2
        StartDaemonThread(self.intervalForever)
        StartDaemonThread(QTermServer(self.conf.termServerPort, self.onTermCommand).Run)
        self.scheduler.start()
        Put(self.Update)

        try:
            MainLoop()
        except KeyboardInterrupt as e:
            pass
        except SystemExit as e:
            raise
        except Exception as e:
            ERROR('', exc_info=True)
            ERROR('Mainloop 发生未知错误：%r', e)
            self.onExit(1, 'unknown-error', e)
            raise SystemExit(1)

    def Stop(self):
        sys.exit(0)

    def Restart(self):
        sys.exit(RESTART)

    def MessageAnalyst(self, Message):
        if type(Message) is not JsonDict:Message = DotDict(Message)
        if 'Message' in Message.type:
            if 'SyncMessage' in Message.type:
                Type = Message.type.replace('SyncMessage','')
                subject = Message.subject
                Sender = ('Group'==Type and self.MemberInfo('get',subject.id, self.conf.qq)) or subject
                Message = Message.messageChain
                Source = Message.pop(0)
                Quote = Message[0].id if Message and Message[0].type == 'Quote' else None
                if Type == 'Friend':INFO(f'{SGR("同步", B4=1)}好友{SGR(subject.nickname,b4=11)}[{SGR(subject.remark,b4=11)}({SGR(subject.id,b4=1)})]{(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.id,b4=12)}):\n{Message}')
                if Type == 'Group':INFO(f'{SGR("同步", B4=4)}群{SGR(subject.name,b4=14)}({SGR(subject.id,b4=4)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.id,b4=12)}):\n{Message}')
                elif Type == 'Temp':INFO(f'{SGR("同步", B4=4)}群{SGR(Sender.group.name,b4=14)}({SGR(Sender.group.id,b4=4)})成员{SGR(Sender.memberName,b4=13)}({SGR(Sender.id,b4=3)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的临时消息({SGR(Source.id,b4=12)}):\n{Message}')
            else:
                Type = Message.type.replace('Message','')
                Sender = Message.sender
                Message = Message.messageChain
                Source = Message.pop(0)
                Quote = Message[0].id if Message and Message[0].type == 'Quote' else None
                if Type == 'Friend':INFO(f'来自好友{SGR(Sender.nickname,b4=11)}[{SGR(Sender.remark,b4=11)}({SGR(Sender.id,b4=1)})]{(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.id,b4=12)}):\n{Message}')
                elif Type == 'Group':INFO(f'来自群{SGR(Sender.group.name,b4=14)}({SGR(Sender.group.id,b4=4)})成员{SGR(Sender.memberName,b4=13)}({SGR(Sender.id,b4=3)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.id,b4=12)}):\n{Message}')
                elif Type == 'Temp':INFO(f'来自群{SGR(Sender.group.name,b4=14)}({SGR(Sender.group.id,b4=4)})成员{SGR(Sender.memberName,b4=13)}({SGR(Sender.id,b4=3)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的临时消息({SGR(Source.id,b4=12)}):\n{Message}')
            # if Sender.id in self.BlackList:return
            self.onQQMessage(Type, Sender, Source, Message)
        elif 'RequestEvent' in Message.type:
            if hasattr(self, 'onQQRequestEvent'):
                operate, msg = self.onQQRequestEvent(Message)
                self.Mirai.event_response(Message, operate, msg)
            bot.Update()
        elif 'Event' in Message.type:
            self.onQQEvent(Message)

    def onQQRequestEvent(self, Message):
        for f in self.slotsTable['onQQRequestEvent']:
            operate, msg = f(self, Message)
            if not operate:
                return operate, msg
        else:
            return operate, msg

    def intervalForever(self):
        while True:
            flag = True
            while self.conf.qq not in self.Mirai.BotList().data:
                time.sleep(60)
                if self.conf.qq in self.Mirai.BotList().data:break
                # os.popen('taskkill /f /im java.exe').read()
                if flag:
                    flag = WARNING(f'qq:{self.conf.qq} 未登录')
            time.sleep(300)
            StartDaemonThread(self.onInterval)
            StartDaemonThread(self.Update)

    def wrap(self, slots):
        def func(*args, **kwargs):
            for f in slots:
                _call(f, self, *args, **kwargs)
        return func

    def AddSlot(self, func):
        self.slotsTable[func.__name__].append(func)
        return func

    def AddSched(self, **triggerArgs):
        def wrapper(func):
            job = lambda: Put(_call, func, self)
            job.__name__ = func.__name__
            j = self.scheduler.add_job(job, CronTrigger(**triggerArgs))
            self.schedTable[func.__module__].append(j)
            return func
        return wrapper

    def Update(self, Type=None):
        if not Type:
            self.Friend = self.List('Friend').data
            self.Group = self.List('Group').data
            self.Member = JsonDict()
            for g in self.Group:
                setattr(self.Member, str(g.id), self.List('Member',g.id).data)
                for m in self.Member[str(g.id)]:
                    delattr(m,'group')
        elif Type in ['Friend', 'Group']:
            setattr(self, Type, self.List(Type).data)
        elif Type == 'Member':
            data = []
            for g in self.Group:
                data[str(g.id)] = self.List('Member',g.id).data
                for m in data[str(g.id)]:
                    delattr(m,'group')
            def member(target):return data[str(target)]
            self.Member=member

    def unplug(self, moduleName, removeJob=True):
        for slots in self.slotsTable.values():
            i = 0
            while i < len(slots):
                if slots[i].__module__ == moduleName:
                    slots[i] = slots[-1]
                    slots.pop()
                else:
                    i += 1

        if removeJob:
            for job in self.schedTable.pop(moduleName, []):
                job.remove()
            self.plugins.pop(moduleName, None)

    def Plug(self, moduleName):
        self.unplug(moduleName)
        try:
            module = Import(moduleName)
        except Exception as e:
            result = '错误：无法加载插件 %s ，%s: %s' % (moduleName, type(e), e)
            ERROR('', exc_info=True)
            ERROR(result)
            self.unplug(moduleName)
        else:
            self.unplug(moduleName, removeJob=False)

            names = []
            for slotName in self.slotsTable.keys():
                if hasattr(module, slotName):
                    self.slotsTable[slotName].append(getattr(module, slotName))
                    names.append(slotName)

            if not names and moduleName not in self.schedTable:
                result = '警告：插件 %s 中没有定义回调函数或定时任务' % moduleName
                WARNING(result)
            else:
                self.plugins[moduleName] = module
                
                jobs = self.schedTable.get(moduleName, [])
                jobNames = [f.func.__name__ for f in jobs]
                result = '成功：加载插件 %s（回调函数%s、定时任务%s）' % \
                         (moduleName, names, jobNames)
                INFO(result)

                if self.Mirai.started and hasattr(module, 'onPlug'):
                    _call(module.onPlug, self)

        return result

    def Unplug(self, moduleName):
        if moduleName not in self.plugins:
            result = '警告：试图卸载未安装的插件 %s' % moduleName
            WARNING(result)
            return result
        else:
            module = self.plugins[moduleName]
            self.unplug(moduleName)
            if hasattr(module, 'onUnplug'):
                _call(module.onUnplug, self)
            result = '成功：卸载插件 %s' % moduleName
            INFO(result)
            return result

    def Plugins(self):
        return list(self.plugins.keys())

def runBot(argv=None):
    if sys.argv[-1] == '--subprocessCall':
        sys.argv.pop()
        bot = QQBot.bot
        bot.Init(argv)
        bot.Run()
    else:
        conf = QConf()

        if conf.daemon:
            conf.Daemonize()

        if sys.argv[0].endswith('py') or sys.argv[0].endswith('pyc'):
            args = [sys.executable] + sys.argv
        else:
            args = sys.argv

        if '--bench' not in args:
            args = args + ['--bench', os.getcwd()]
        args = args + ['--qq', str(conf.qq)]
        args = args + ['--subprocessCall']

        while True:
            p = subprocess.Popen(args)
            code = p.wait()
            if code == 0:
                INFO('QQBot 正常停止')
                sys.exit(code)
            elif code == RESTART:
                INFO('1 秒后重新启动 QQBot （自动登陆，qq=%s）', args[-2])
                time.sleep(1)
            else:
                CRITICAL('QQBOT 异常停止（code=%s）', code)
                if conf.restartOnOffline:
                    args[-2] = '0'
                    INFO('5秒后重新启动 QQBot （手动登录）')
                    time.sleep(5)
                else:
                    sys.exit(code)

def RunBot():
    try:
        runBot()
    except KeyboardInterrupt:
        sys.exit(1)

bot = QQBot()
QQBot.bot = bot
QQBotSlot = bot.AddSlot
QQBotSched = bot.AddSched
QQBot.__init__ = None