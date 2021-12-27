# -*- coding: utf-8 -*-

import os, sys, time, subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from collections import defaultdict

from mainloop import MainLoop, Put
from miraiapi import MiraiApi, RequestError
from common import Import, StartDaemonThread
from qconf import QConf
from utf8logger import INFO, CRITICAL, ERROR, PRINT, WARNING

RESTART = 201

def _call(func, *args, **kwargs):
    try:
        StartDaemonThread(func, *args, **kwargs)
    except Exception as e:
        ERROR('', exc_info=True)
        ERROR('执行 %s.%s 时出错，%s', func.__module__, func.__name__, e)

class QQBot():
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
        self.plugins = {}

    def init(self, argv=None):
        for name, slots in self.slotsTable.items():
            setattr(self, name, self.wrap(slots))
        self.slotsTable['onQQRequestEvent'] = []
        self.conf = QConf(argv)
        self.conf.Display()

        self.Mirai = MiraiApi(self.conf.qq, self.conf.verifyKey, self.conf.host, self.conf.port)
        while not self.Mirai.started:pass

        self.MessageFromId = self.Mirai.MessageFromId
        self.SendMessage = self.Mirai.SendMessage
        self.Nudge = self.Mirai.Nudge
        self.Recall = self.Mirai.Recall
        self.List = self.Mirai.List
        self.Profile = self.Mirai.Profile
        self.DeleteFriend = self.Mirai.DeleteFriend
        self.Mute = self.Mirai.Mute
        self.kick = self.Mirai.kick
        self.quit = self.Mirai.quit
        self.MuteAll = self.Mirai.MuteAll
        self.SetEssence = self.Mirai.SetEssence
        self.GroupConfig = self.Mirai.GroupConfig
        self.MemberInfo = self.Mirai.MemberInfo
        self.FileList = self.Mirai.FileList
        self.FileInfo = self.Mirai.FileInfo
        self.FileMkdir = self.Mirai.FileMkdir
        self.FileDelete = self.Mirai.FileDelete
        self.FileMove = self.Mirai.FileMove
        self.FilereName = self.Mirai.FilereName
        self.FileUpload = self.Mirai.FileUpload
        self.Upload = self.Mirai.Upload

        for pluginName in self.conf.plugins:
            self.Plug(pluginName)

    def Run(self):
        self.onStartupComplete()
        self.onPlug()

        StartDaemonThread(self.pollForever)
        StartDaemonThread(self.intervalForever)
        self.scheduler.start()
        Put(self.Update)

        try:
            MainLoop()
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

    # child thread 1
    def pollForever(self):
        while self.Mirai.started:
            try:
                result = self.Mirai.GetMessage()
            except RequestError:
                Put(sys.exit)
                break
            except:
                ERROR('qsession.Poll 方法出错', exc_info=True)
            else:
                if not result:continue
                for r in result:
                    Put(self.MessageAnalyst, r)

    def MessageAnalyst(self, Message):
        if 'Message' in Message.type:
            Type = Message.type.replace('Message','')
            Sender = Message.sender
            Message = Message.messageChain
            Source = Message.pop(0)
            if hasattr(Sender, 'group'):
                INFO(f'来自 {Type} {Sender.group.name} {Sender.memberName} 的消息({Source.id}):')
            else:
                INFO(f'来自 {Type} {Sender.nickname} 的消息({Source.id}):')
            INFO(str(Message))
            self.onQQMessage(Type, Sender, Source, Message)
        elif 'RequestEvent' in Message.type:
            if hasattr(self, 'onQQRequestEvent'):
                operate, msg = self.onQQRequestEvent(Message)
                self.Mirai.Event_response(Message, operate, msg)
        elif 'Event' in Message.type:
            self.onQQEvent(Message)

    def onQQRequestEvent(self, Message):
        for f in self.slotsTable['onQQRequestEvent']:
            operate, msg = f(self, Message)
            if not operate:
                return operate, msg
        else:
            return operate, msg

    # child thread 2
    def intervalForever(self):
        while True:
            time.sleep(300)
            Put(self.onInterval)

    def Command(self):
        while True:pass

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

    def Update(self):
        self.Friend = self.List('Friend')
        self.Group = self.List('Group')
        self.Member = {}
        for g in self.Group:
            self.Member[g.id] = self.List('Member',g.id)
            for m in self.Member[g.id]:
                delattr(m,'group')

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
        bot = QQBot._bot
        bot.init(argv)
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

_bot = QQBot()
QQBot._bot = _bot
QQBotSlot = _bot.AddSlot
QQBotSched = _bot.AddSched
QQBot.__init__ = None