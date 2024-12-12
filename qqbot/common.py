# -*- coding: utf-8 -*-

import json, subprocess, threading, sys, platform, os, base64, io

class JsonDict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError:
            return
    def __setattr__(self, attr, value):
        self[attr] = value
    def __delattr__(self, attr):
        try:
            del self[attr]
        except KeyError:
            return

def DotDict(obj:dict|list|str|io.IOBase={}) -> JsonDict:
    if isinstance(obj, (dict, list)):
        obj = json.dumps(obj)
    if isinstance(obj, io.IOBase):
        obj = obj.read()
    return json.loads(obj, object_hook=JsonDict)

jsonload = json.load
jsondump = json.dump
jsonloads = json.loads
jsondumps = json.dumps

STR2BYTES = lambda s: s.encode('utf8')
BYTES2STR = lambda s: s.decode('utf8')

b64enc = lambda s,encoding="utf-8":base64.b64encode(s.encode(encoding)).decode().replace('=','') if isinstance(s,str) else base64.b64encode(s).decode().replace('=','')
b64dec = lambda s:base64.b64decode((s+'='*(len(s)%4)).encode()).decode() if isinstance(s,str) else base64.b64decode((s.decode()+'='*(len(s)%4)).encode()).decode()
b64dec2b = lambda s:base64.b64decode((s+'='*(len(s)%4)).encode()) if isinstance(s,str) else base64.b64decode((s.decode()+'='*(len(s)%4)).encode())

def secs2hours(secs):
    M, S = divmod(secs, 60)
    H, M =divmod(M, 60)
    D, H =divmod(H, 24)
    return f"{D} {H}:{M}:{S}"

def B2B(B):
    l = []
    while True:
        B, A = divmod(B, 1024)
        l.append(A)
        if B <= 1024:break
    l.append(B)
    l = list(zip(l, ' KMGTPEZY'))
    l.reverse()
    return ','.join([f'{B}{S}B' for B, S in l])

def SGR(text:str,setup:str='',b4:int=None,B4:int=None,b8:int=None,B8:int=None,r:int=None,g:int=None,b:int=None,R:int=None,G:int=None,B:int=None) -> str:
    '''# Select Graphic Rendition 
    text 文本
    - setup 字体设置组合
        - b 加粗或增亮
        - l 增暗
        - i 斜体
        - u 下划线
        - uu 双下划线
        - d 删除线
        - t 上划线
        - f 闪烁
        - r 反转字色和底色
        - h 隐藏
    - b4 4-bit 字色 | B4 4-bit 底色: 0-7 增亮 10-17
    - b8 8-bit 字色 | B8 8-bit 底色: 0-255
    - r,g,b RGB字色 | R,G,G RGB底色'''
    conf = []
    if 'b'in setup.lower():conf.append('1') # 加粗或增亮
    if 'l'in setup.lower():conf.append('2') # 增暗
    if 'i'in setup.lower():conf.append('3') # 斜体
    if 'u'in setup.lower():conf.append('4') # 下划线
    if 'uu'in setup.lower():conf.append('21') # 双下划线
    if 'd'in setup.lower():conf.append('9') # 删除线
    if 't'in setup.lower():conf.append('53') # 上划线
    if 'f'in setup.lower():conf.append('5') # 闪烁
    if 'r'in setup.lower():conf.append('7') # 反显
    if 'h'in setup.lower():conf.append('8') # 隐藏
    if b4 in range(0,8) or b4 in range(10,18):conf.append(str(b4+30 if b4 < 9 else b4+80)) # 0-7 之间 黑、红、绿、黄、蓝、紫、青、白 10-17 增亮
    if B4 in range(0,8) or B4 in range(10,18):conf.append(str(B4+40 if B4 < 9 else B4+90)) # 0-7 之间 黑、红、绿、黄、蓝、紫、青、白 10-17 增亮
    if b8 in range(256):conf += ['38','5',str(b8)] # 0-255 之间 8-bit 色彩
    if B8 in range(256):conf += ['48','5',str(B8)] # 0-255 之间 8-bit 色彩
    if any([i in range(256) for i in [r,g,b]]):conf += ['38','2',str(r or 0),str(g or 0),str(b or 0)]
    if any([i in range(256) for i in [R,G,B]]):conf += ['48','2',str(R or 0),str(G or 0),str(B or 0)]
    return f'\033[{";".join(conf)}m{text}\033[0m' if 'Windows-10' in platform.platform() else text

def isSpace(b):
    return b in [' ', '\t', '\n', '\r', 32, 9, 10, 13]

def Partition(msg):
    msg = msg.encode('utf8')

    n = 720

    if len(msg) < n:
        f, b = msg, b''
    else:
        for i in range(n-1, n-101, -1):
            if isSpace(msg[i]):
                f, b = msg[:i+1], msg[i+1:]
                break
        else:
            for i in range(n-1, n-301, -1):
                x = msg[i]
                if (x >> 6) != 2:
                    f, b = msg[:i], msg[i:]
                    break
            else:
                f, b = msg[:n], msg[n:]

    return f.decode('utf8'), b.decode('utf8')

def HasCommand(procName):
    return subprocess.call(['which', procName], stdout=subprocess.PIPE) == 0

def StartThread(target, *args, **kwargs):
    threading.Thread(target=target, args=args, kwargs=kwargs).start()

def StartDaemonThread(target, *args, **kwargs):
    threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True).start()

class LockedValue(object):
    def __init__(self, initialVal=None):
        self.val = initialVal
        self.lock = threading.Lock()

    def setVal(self, val):
        with self.lock:
            self.val = val

    def getVal(self):
        with self.lock:
            val = self.val
        return val

# usage: CallInNewConsole(['python', 'qterm.py'])
def CallInNewConsole(args=None):
    args = sys.argv[1:] if args is None else args

    if not args:
        return 1

    osName = platform.system()

    if osName == 'Windows':
        return subprocess.call(['start'] + list(args), shell=True)

    elif osName == 'Linux':
        cmd = subprocess.list2cmdline(args)
        if HasCommand('mate-terminal'):
            args = ['mate-terminal', '-e', cmd]
        elif HasCommand('gnome-terminal'):
            args = ['gnome-terminal', '-e', cmd]
        elif HasCommand('xterm'):
            args = ['sh', '-c', 'xterm -e %s &' % cmd]
        else:
            return 1
            # args = ['sh', '-c', 'nohup %s >/dev/null 2>&1 &' % cmd]
        return subprocess.call(args, preexec_fn=os.setpgrp)

    elif osName == 'Darwin':
        return subprocess.call(['open','-W','-a','Terminal.app'] + list(args))

    else:
        return 1
        # return subprocess.Popen(list(args) + ['&'])

def search(name,mod=None,path=os.getcwd(),dir_path=False): # 查找文件返回路径
    # mod - 搜索模式
    #    dn 搜索文件夹包含的文字
    #    fn 搜索文件包含的文字
    if type(name) is not str:name = str(name)
    def return_dir(root,name,dir_path=False):
        if dir_path:return root
        return os.path.join(root, name)

    for root, dirs, files in os.walk(path):  # path 为根目录
        if mod == None and (name in dirs or name in files): # 绝对名搜索
            return return_dir(dir_path, root, name)
        elif mod == 'dn': # 文件夹包含文字
            for d in dirs:
                if name in f:return return_dir(root, d)
        elif mod == 'fn': # 文件包含文字
            for f in files:
                if name in f:return return_dir(root, f, dir_path)
        else:
            raise

def LeftTrim(s, head):
    if s.startswith(head):
        return s[:len(head)]
    else:
        return s

def AutoTest():
    with open(sys.argv[1], 'rb') as f:
        for line in f.read().split(b'\n'):
            line = BYTES2STR(line.strip())
            if not line:
                continue
            elif line.startswith('#'):
                print(line)
            else:
                print('>>> '+line)
                os.system(line)
                sys.stdout.write('\npress enter to continue...')
                input()
                sys.stdout.write('\n')

def IsMainThread():
    return threading.current_thread().name == 'MainThread'

import importlib
reload = importlib.reload

# import module / import package.module
# Import('module') / Import('package.module')
def Import(moduleName):
    if moduleName in sys.modules:
        reload(sys.modules[moduleName])
    else:
        __import__(moduleName)
    return sys.modules[moduleName]


import urllib.parse
Unquote = urllib.parse.unquote

def mydump(fn, d):
    with open(fn, 'wb') as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

def UniIter(s):
    return zip(map(ord, s), s)

# http://pydev.blogspot.com/2013/01/python-get-parent-process-id-pid-in.html
# Python: get parent process id (pid) in windows
# Below is code to monkey-patch the os module to provide a getppid() function
# to get the parent process id in windows using ctypes (note that on Python 3.2,
# os.getppid() already works and is available on windows, but if you're on an
# older version, this can be used as a workaround).
import os

if not hasattr(os, 'getppid'):
    import ctypes

    TH32CS_SNAPPROCESS = int(0x02)
    CreateToolhelp32Snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot
    GetCurrentProcessId = ctypes.windll.kernel32.GetCurrentProcessId

    MAX_PATH = 260

    _kernel32dll = ctypes.windll.Kernel32
    CloseHandle = _kernel32dll.CloseHandle

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.c_ulong),
            ("cntUsage", ctypes.c_ulong),
            ("th32ProcessID", ctypes.c_ulong),
            ("th32DefaultHeapID", ctypes.c_int),
            ("th32ModuleID", ctypes.c_ulong),
            ("cntThreads", ctypes.c_ulong),
            ("th32ParentProcessID", ctypes.c_ulong),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.c_ulong),

            ("szExeFile", ctypes.c_wchar * MAX_PATH)
        ]

    Process32First = _kernel32dll.Process32FirstW
    Process32Next = _kernel32dll.Process32NextW

    def getppid():
        '''
        :return: The pid of the parent of this process.
        '''
        pe = PROCESSENTRY32()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
        mypid = GetCurrentProcessId()
        snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)

        result = 0
        try:
            have_record = Process32First(snapshot, ctypes.byref(pe))

            while have_record:
                if mypid == pe.th32ProcessID:
                    result = pe.th32ParentProcessID
                    break

                have_record = Process32Next(snapshot, ctypes.byref(pe))

        finally:
            CloseHandle(snapshot)

        return result

    os.getppid = getppid

daemonable = hasattr(os, 'fork')

def daemonize(stdoutfile=None, stderrfile=None):
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError:
        print("fork error!!!")
        sys.exit(1)

    os.setsid()

    try:
        pid = os.fork()
        if pid > 0:
            print("PID: %d" % pid)
            sys.exit(0)
    except OSError:
        print("fork error!!!")
        sys.exit(1)

    # os.chdir("/")
    os.umask(0)    

#    dev_null = open("/dev/null", "r+")
#    os.dup2(dev_null.fileno(), sys.stdout.fileno())
#    os.dup2(dev_null.fileno(), sys.stderr.fileno())
#    os.dup2(dev_null.fileno(), sys.stdin.fileno())

    dev_null = open("/dev/null", "r+")

    if stdoutfile:
        stdout = open(stdoutfile, "w")
    else:
        stdout = dev_null

    if stderrfile:
        stderr = open(stderrfile, "w")
    else:
        stderr = stdout

    stdin = dev_null

    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())