# -*- coding: utf-8 -*-

import sys, os
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if p not in sys.path:
    sys.path.insert(0, p)

version = 'v0.1'

sampleConfStr = '''
{
    # QQBot 的配置文件
    # 使用 -s someone 启动程序时，依次加载：
    #     根配置 -> 默认配置 -> 用户 someone 的配置 -> 命令行参数配置
    # 使用 qqbot 启动程序时，依次加载：
    #     根配置 -> 默认配置 -> 命令行参数配置

    # 用户 someone 的配置
    "默认配置" : {

        # QQBot-term （HTTP-API） 服务器端口号（该服务器监听 IP 为 127.0.0.1 ）
        # 设置为 0 则不会开启本服务器（此时 qq 命令和 HTTP-API 接口都无法使用）。
        "termServerPort" : 8188,

        # Mirai http 服务器地址，请设置为公网地址或localhost
        "host" : "localhost",

        # Mirai http api 的端口
        "httpport" : 5700,

        # Mirai websocket api 的端口
        "wsport" : 5800,

        # Mirai http api 验证密钥
        "token" : "VerifyKey",

        # 显示/关闭调试信息
        "debug" : False,

        # QQBot 异常后自动重启
        "restartOnOffline" : True,

        # 在后台运行 qqbot ( daemon 模式)
        "daemon": False,

        # 插件目录
        "pluginPath" : ".",

        # 启动时需加载的插件
        "plugins" : ['admin']

    },

    # 可以在 默认配置 中配置所有用户都通用的设置
    "someone" : {
        "termServerPort" : 8188,
        "host" : "localhost",
        "httpport" : 5700,
        "wsport" : 5800,
        "token" : "VerifyKey",
        "debug" : False,
        "restartOnOffline" : False,
        "daemon": False,
        "pluginPath" : ".",
        "plugins" : ['admin']
    },

    # # 注意：根配置是固定的，用户无法修改（在本文件中修改根配置不会生效）
    # "根配置" : {
    #     "termServerPort" : 8188,
    #     "host" : "localhost",
    #     "httpport" : 5700,
    #     "wsport" : 5800,
    #     "debug" : False,
    #     "restartOnOffline" : True,
    #     "daemon" : False,
    #     "pluginPath" : "",
    #     "plugins" : ['admin']
    # },

}
'''

rootConf = {
        "termServerPort" : 8188,
        "host" : "localhost",
        "httpport" : 5700,
        "wsport" : 5800,
        "token" : "VerifyKey",
        "debug" : False,
        "restartOnOffline" : True,
        "daemon": False,
        "pluginPath" : ".",
        "plugins" : ['admin']
    }

if sys.argv[0].endswith('.py') or sys.argv[0].endswith('.pyc'):
    progname= sys.executable + ' ' + sys.argv[0]
else:
    progname = sys.argv[0]

usage = '''\
QQBot 机器人

用法: {PROGNAME} [-h] [-d] [-nd] [-dm] [-ndm]
          [-c CONF] [-r] [-nr] [-tp TERMSERVERPORT]
          [-ip HOST] [-hp HTTPPORT] [-wp WSPORT]
          [-pp PLUGINPATH] [-pl PLUGINS]

选项:
  通用:
    -h,   --help            显示此帮助页面
    -d,   --debug           启用调试模式
    -nd,  --nodebug         停用调试模式
    -dm,  --daemon          以 daemon 模式运行
    -ndm, --nodaemon        不以 daemon 模式运行

  工作目录：
    -b BENCH, --bench BENCH 指定工作目录，默认为 “./”
                            qqbot 运行时将在工作目录下搜索配置文件
                            （v0.x.conf），在工作目录以下的 plugins 目录中搜
                            索插件。

  登陆 OneBot host http ws 服务器设置:
    -s SETUP, --setup SETUP 指定一个配置文件项目以导入设定。
                            USER 指的是配置文件项目的名称。
                            注意: 所有从命令行中指定的参数设定的优先级都会高于
                            从配置文件中获取的设定。
    -ip HOST, --host HOST   指定 OneBot 服务在哪个IP地址上。
    -hp HTTPPORT, --httpport HTTPPORT
                            更改 OneBot 的监听 HTTPPORT 端口到。
                            默认的监听端口是 5700 (TCP)。
    -wp WSPORT, --wsport WSPORT
                            更改 OneBot 的监听 WSPORT 端口到。
                            默认的监听端口是 5800 (TCP)。
    -t TOKEN, --token TOKEN
                            设置 OneBot 认证 TOKEN 。

  QTerm本地控制台服务:
    -tp TERMSERVERPORT, --termServerPort TERMSERVERPORT
                            更改QTerm控制台的监听端口到 TERMSERVERPORT 。
                            默认的监听端口是 8188 (TCP)。

  掉线重新启动:
    -r, --restartOnOffline  在异常时自动重新启动。
    -nr, --norestart        在掉线时不要重新启动。

  其他：
    -pp PLUGINPATH, --pluginPath PLUGINPATH
                            添加插件目录
    -pl PLUGINS, --plugins PLUGINS
                            设置启动时需加载的插件

版本:
  {VERSION}\
'''.format(PROGNAME=progname,  VERSION=version)

import os, sys, ast, argparse, platform, time, pkgutil

from utf8logger import SetLogLevel, INFO, PRINT, ERROR
from common import STR2BYTES, BYTES2STR
from common import daemonize, daemonable

class ConfError(Exception):
    pass

class QConf(object):
    def __init__(self, argv=None):
        self.version = version
        self.readCmdLine(argv)
        self.readConfFile()
        self.configure()

    def readCmdLine(self, argv):
        if argv is None:
            argv = sys.argv[1:]

        parser = argparse.ArgumentParser(add_help=False)

        parser.add_argument('-h', '--help', action='store_true')

        parser.add_argument('-b', '--bench')

        parser.add_argument('-s', '--setup', default=None)

        parser.add_argument('-ip', '--host')

        parser.add_argument('-hp', '--httpport', type=int)

        parser.add_argument('-wp', '--wsport', type=int)

        parser.add_argument('-t', '--token', type=str, default=None)

        parser.add_argument('-tp', '--termServerPort', type=int)

        parser.add_argument('-d', '--debug', action='store_true', default=None)

        parser.add_argument('-nd', '--nodebug', action='store_true')

        parser.add_argument('-dm', '--daemon', action='store_true', default=None)

        parser.add_argument('-ndm', '--nodaemon', action='store_true')

        parser.add_argument('-r', '--restartOnOffline', action='store_true', default=None)

        parser.add_argument('-nr', '--norestart', action='store_true')

        parser.add_argument('-pp', '--pluginPath')

        parser.add_argument('-pl', '--plugins')

        try:
            opts = parser.parse_args(argv)
        except:
            PRINT(usage)
            sys.exit(1)

        if opts.help:
            PRINT(usage)
            sys.exit(0)

        if opts.nodebug:
            opts.debug = False

        if opts.norestart:
            opts.restartOnOffline = False

        if opts.nodaemon:
            opts.daemon = False

        delattr(opts, 'nodebug')
        delattr(opts, 'norestart')
        delattr(opts, 'nodaemon')

        if not opts.bench:
            opts.bench = os.getcwd()

        opts.bench = os.path.abspath(opts.bench)
        sys.path.insert(0, opts.bench)

        if not os.path.exists(opts.bench):
            try:
                os.mkdir(opts.bench)
            except Exception as e:
                PRINT('无法创建工作目录 %s ， %s' % (opts.bench, e))
                sys.exit(1)
        elif not os.path.isdir(opts.bench):
            PRINT('无法创建工作目录 %s ' % opts.bench)
            sys.exit(1)

        if opts.plugins:
            opts.plugins = opts.plugins.split(',')

        for k, v in list(opts.__dict__.items()):
            if getattr(self, k, None) is None:
                setattr(self, k, v)

    def readConfFile(self):
        confPath = self.ConfPath()
        conf = rootConf.copy()

        if os.path.exists(confPath):
            try:
                with open(confPath, 'rb') as f:
                    cusConf = ast.literal_eval(BYTES2STR(f.read()))

                if type(cusConf) is not dict:
                    raise ConfError('文件内容必须是一个 dict')

                if type(cusConf.get('默认配置', {})) is not dict:
                    raise ConfError('默认配置必须是一个 dict')

                if self.setup is not None:
                    if self.setup not in cusConf:
                        raise ConfError('设置 %s 不存在' % self.setup)
                    elif type(cusConf[self.setup]) is not dict:
                        raise ConfError('设置 %s 的配置必须是一个 dict'%self.setup)
                    else:
                        names = ['默认配置', self.setup]
                else:
                    names = ['默认配置']

                for name in names:
                    for k, v in list(cusConf.get(name, {}).items()):
                        if k not in conf:
                            raise ConfError('不存在的配置选项 %s.%s ' % (name, k))
                        elif type(v) is not type(conf[k]):
                            t = type(conf[k]).__name__
                            raise ConfError('%s.%s 必须是一个 %s' % (name, k, t))
                        else:
                            conf[k] = v

            except (IOError, SyntaxError, ValueError, ConfError) as e:
                PRINT('配置文件 %s 错误: %s\n' % (confPath, e), end='')
                sys.exit(1)

        else:
            PRINT('未找到配置文件“%s”，将使用默认配置' % confPath)
            try:
                with open(confPath, 'wb') as f:
                    f.write(STR2BYTES(sampleConfStr))
            except IOError:
                pass
            else:
                PRINT('已创建一个默认配置文件“%s”' % confPath)

            if self.setup is not None:
                PRINT('配置 %s 不存在\n' % self.setup, end='')
                sys.exit(1)

        for k, v in list(conf.items()):
            if getattr(self, k, None) is None:
                setattr(self, k, v)

        if self.pluginPath and not os.path.isdir(self.pluginPath):
            PRINT('配置文件 %s 错误: 插件目录 “%s” 不存在\n' % \
                  (confPath, self.pluginPath), end='')
            sys.exit(1)

    def Config(self, fn):
        return os.path.join(self.config, fn)

    def configure(self):
        c = self.absPath('config')
        if not os.path.exists(c):
            os.mkdir(c)
        if os.path.isdir(c):
            self.config = c
        else:
            self.config = None

        p = self.absPath('plugins')
        if not os.path.exists(p):
            os.mkdir(p)

        if os.path.isdir(p):
            if p not in sys.path:
                sys.path.insert(0, p)
            self.pluginPath = p
        else:
            self.pluginPath = None

        SetLogLevel(self.debug and 'DEBUG' or 'INFO')

    def Display(self):
        INFO(f'QQBot-{self.version}')
        INFO(f'Python {platform.python_version()}')
        INFO(f'工作目录：{self.bench}')
        INFO(f'配置文件：{self.ConfPath()}')
        INFO(f'配置名：{self.setup or "无"}')
        INFO(f'命令行服务器端口号：{self.termServerPort or "无"}')
        INFO(f'OneBot服务器 ip ：{self.host or "localhost"}')
        INFO(f'OneBot服务器 HTTP 端口号：{self.httpport or "5700"}')
        INFO(f'OneBot服务器 WS 端口号：{self.wsport or "5800"}')
        INFO(f'OneBot服务器 token：{self.token and self.token[0] + "*****" + self.token[-1]}')
        INFO(f'调试模式：{self.debug and "开启" or "关闭"}')
        INFO(f'掉线后自动重启：{self.restartOnOffline and "是" or "否"}')
        INFO(f'后台模式（daemon 模式）：{self.daemon and "是" or "否"}')
        self.pluginPath and INFO(f'插件目录：{self.pluginPath}')
        INFO(f'启动时需要加载的插件：{self.plugins}')

    def absPath(self, rela):
        return os.path.join(self.bench, rela)

    def ConfPath(self):
        return self.absPath('%s.conf' % self.version[:4])

    def PicklePath(self):
        return self.absPath(
            '%s-py%s-%d.pickle' %
            (self.version[:4], sys.version_info.major, self.setup)
        )

    def Daemonize(self):
        if daemonable:
            logfile = self.absPath('daemon-%d.log' % self.setup)
            PRINT('将以 daemon 模式运行， log 文件： %s' % logfile)
            daemonize(logfile)
        else:
            PRINT('错误：无法以 daemon 模式运行')
            sys.exit(1)

if __name__ == '__main__':
    # QConf().Display()
    # print('')
    conf = QConf(['-ip', 'xxx', '-hp', '6700', '-wp', '6800', '--daemon']).Display()