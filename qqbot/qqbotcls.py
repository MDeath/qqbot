# -*- coding: utf-8 -*-

import os, sys, time, subprocess
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from collections import defaultdict

from mainloop import MainLoop, Put
from onebotapi import OneBotApi, RequestError
from common import DotDict, Import, JsonDict, StartDaemonThread, SGR
from qconf import QConf
from qdb import DataBase
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
            'onInterval':[],
            'onQQMessage':[],
            'onQQNotice':[],
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

        self.db = DataBase('QDB.db')
        self.OneBot = OneBotApi(self.conf.token, self.conf.host, self.conf.httpport, self.conf.wsport)

        self.LoginInfo = self.OneBot.LoginInfo
        self.List = self.OneBot.List
        self.Info = self.OneBot.Info
        self.SystemMsg = self.OneBot.SystemMsg
        self.SendMsg = self.OneBot.SendMsg
        self.GetMsg = self.OneBot.GetMsg
        self.Recall = self.OneBot.Recall
        self.HistoryMsg = self.OneBot.HistoryMsg
        self.GetForward = self.OneBot.GetForward
        self.GetImage = self.OneBot.GetImage
        self.GetRecord = self.OneBot.GetRecord
        self.GetFile = self.OneBot.GetFile
        self.SetGroupName = self.OneBot.SetGroupName
        self.SetGroupAdmin = self.OneBot.SetGroupAdmin
        self.SetGroupCard = self.OneBot.SetGroupCard

    def Run(self):
        for pluginName in self.conf.plugins:
            self.Plug(pluginName)

        self.onPlug()

        # 子线程 1 上报处理
        StartDaemonThread(self.OneBot.pollForever, self.eventAnalyst)
        # 子线程 2 五分钟定时任务
        StartDaemonThread(self.intervalForever)
        StartDaemonThread(QTermServer(self.conf.termServerPort, self.onTermCommand).Run)
        self.scheduler.start()
        while not self.OneBot.started:pass
        self.qq = self.OneBot.qq
        self.Friend = self.OneBot.Friend
        self.Group = self.OneBot.Group
        self.Member = self.OneBot.Member

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

    def eventAnalyst(self, event):
        DEBUG(event)
        if event.post_type.startswith('message'): # 消息类型
            self.MessageAnalyst(event)
        elif event.post_type == 'notice':
            self.onQQNotice(event)
        elif event.post_type == 'request':
            self.RequestAnalyst(event)
        else:
            WARNING(f'PostType omission: {event.post_type}\n{event}')

    def MessageAnalyst(self, event): # 上报处理
        for msg in event.message: # 消息链处理
            if 'data' not in msg:continue
            if 'type' in msg.data:msg.data.data_type = msg.data.pop('type') # data内有type转成data_type
            msg.update(msg.pop('data')) # 把data往上提取一层
        Quote = event.message[0].id if event.message and event.message[0].type == 'reply' else None # 提取回复的信息ID
        if event.message_type == 'private': # 好友消息处理
            Type = 'friend' # 上报
            Source = JsonDict(time=event.time, message_id=event.message_id, target=event.target_id)
            Source.update(self.Friend(user_id=event.target_id)[0])
            Sender = self.Friend(user_id=event.sender.user_id)[0]
            if 'post_type' in event and event.post_type.endswith('sent'):INFO(f'{SGR("同步", B4=1)}好友{SGR(Source.user_name,b4=11)}[{SGR(Source.user_remark,b4=11)}({SGR(Source.user_id,b4=1)})]{(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.message_id,b4=12)}):\n{event.message}')
            else:INFO(f'来自好友{SGR(Sender.user_name,b4=11)}[{SGR(Sender.user_remark,b4=11)}({SGR(Sender.user_id,b4=1)})]{(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.message_id,b4=12)}):\n{event.message}')
                
        elif event.message_type == 'group' and event.sub_type == 'normal': # 群消息处理
            Type = event.message_type
            Source = JsonDict(time=event.time, message_id=event.message_id, target=event.group_id)
            Source.update(self.Group(group_id=event.group_id)[0])
            Sender = self.Member(group_id=event.group_id,user_id=event.user_id)[0]
            if 'post_type' in event and event.post_type.endswith('sent'):INFO(f'{SGR("同步", B4=4)}群{SGR(Source.group_name,b4=14)}({SGR(Source.group_id,b4=4)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.message_id,b4=12)}):\n{event.message}')
            else:INFO(f'来自群{SGR(Source.group_name,b4=14)}({SGR(Source.group_id,b4=4)})成员{SGR(Sender.user_name,b4=13)}({SGR(Sender.user_id,b4=3)}){(Quote and "回复("+SGR(Quote,b4=2)+")") or ""}的消息({SGR(Source.message_id,b4=12)}):\n{event.message}')
        else: # 其他类型
            WARNING(f'MessageSubType omission: {event.sub_type}\n{event}')
            return
        self.onQQMessage(Type, Sender, Source, event.message)

    def RequestAnalyst(self, Request):
        if Request.request_type == 'friend':
            INFO(f'来自 {Request.user_id} 的好友申请，事件标识：{Request.flag}')
        if Request.request_type == 'group':
            INFO(f'来自 {Request.user_id} 的{"申请" if Request.sub_type else "邀请"}，{"申请" if Request.sub_type else "邀请"}加入{Request.group_id}，事件标识：{Request.flag}')
        approve, re = self.onQQRequestEvent(Request)
        self.OneBot.request_response(Request, approve, re)

    def onQQRequestEvent(self, Request):
        approve, re = None, None
        for f in self.slotsTable['onQQRequestEvent']:
            approve, re = f(self, Request)
            if not approve:
                return approve, re
        else:
            return approve, re

    def intervalForever(self):
        while True:
            time.sleep(300)
            StartDaemonThread(self.onInterval)

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

                if self.OneBot.started and hasattr(module, 'onPlug'):
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
        args = args + ['--subprocessCall']

        while True:
            p = subprocess.Popen(args)
            code = p.wait()
            if code == 0:
                INFO('QQBot 正常停止')
                sys.exit(code)
            elif code == RESTART:
                INFO('1 秒后重新启动 QQBot')
                time.sleep(1)
            else:
                CRITICAL('QQBOT 异常停止（code=%s）', code)
                if conf.restartOnOffline:
                    INFO('5秒后重新启动 QQBot')
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
if __name__ == '__main__':
    runBot(['-t','0123456789','-ip','localhost','-hp','5700','-wp','5800','-d'])