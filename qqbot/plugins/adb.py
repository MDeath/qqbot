import os

import soup
from qqbotcls import QQBotSched
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
from admin import admin_ID

ADB_PATH = r'Z:\Tools\android\Platform-Tools\adb.exe' # * ADB 工具路径
ADB = lambda s:f'{ADB_PATH} {s}' 
adb = lambda s:os.popen(ADB(s)).read()
SERIAL = '192.168.0.25:5555' # * SHELL 默认设备
TCPIP = '192.168.0.25:5555'
SHELL = lambda s:ADB(fr'-s {SERIAL} shell {s}')
shell = lambda s:os.popen(SHELL(s)).read()
DEVICES = lambda:{line.split()[0]:{info.split(':')[0]:info.split(':')[1] for info in line.split()[2:]} for line in os.popen(ADB('devices -l')).read().splitlines()[1:-1]}

@QQBotSched(year=None, 
            month=None, 
            day=None, 
            week=None, 
            day_of_week=None, 
            hour=None, 
            minute=','.join([str(n) for n in range(0,60,3)]),
            second=None, 
            start_date=None, 
            end_date=None, 
            timezone=None)
def Chick(bot): # 免死金牌
    if bot.OneBot.started:return
    if SERIAL not in DEVICES():return
    WARNING('开始尝试心肺复苏')
    shell(r'monkey -p moe.fuqiuluo.shamrock -c android.intent.category.LAUNCHER 1')
    shell(r'monkey -p com.tencent.mobileqq -c android.intent.category.LAUNCHER 1')


def onPlug(bot):
    if SERIAL not in DEVICES():
        if TCPIP:
            if 'failed to connect' in adb(f'connect {TCPIP}'):bot.Unplug(__name__)
        else:bot.Unplug(__name__)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    ADB 命令行
    管理员使用 adb 开头
    SHELL 命令行
    管理员使用 shell 开头控制设备
    '''
    Text = ''
    for msg in Message: 
        if msg.type == 'text':Text += msg.text

    if Sender.user_id in [f.user_id for f in admin_ID()]:
        if Text.lower().startswith('adb') and Text.lower().strip() != 'adb':bot.SendMsg(Type,Source.target,soup.Text(adb(Text[3:]) or '空'), reply=Source.message_id)
        if Text.lower().startswith('shell') and Text.lower().strip() != 'shell':bot.SendMsg(Type,Source.target,soup.Text(shell(Text[5:]) or '空'), reply=Source.message_id)