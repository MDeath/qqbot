# -*- coding: utf-8 -*-

import sys, os
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if p not in sys.path:
    sys.path.insert(0, p)

import sys, logging
import logging

def equalUtf8(coding):
    return coding is None or coding.lower() in ('utf8', 'utf-8', 'utf_8')

class CodingWrappedWriter(object):
    def __init__(self, coding, writer):
        self.flush = getattr(writer, 'flush', lambda : None)
        
        wcoding = getattr(writer, 'encoding', None)
        wcoding = 'gb18030' if (wcoding in ('gbk', 'cp936')) else wcoding

        if not equalUtf8(wcoding):
            self._write = lambda s: writer.write(
                s.decode(coding).encode(wcoding, 'ignore')
            )
        else:
            self._write = writer.write
    
    def write(self, s):
        self._write(s)
        self.flush()

# reference http://blog.csdn.net/jim7424994/article/details/22675759
import io
if hasattr(sys.stdout, 'buffer') and (not equalUtf8(sys.stdout.encoding)):
    if sys.stdout.encoding in ('gbk', 'cp936'):
        coding = 'gb18030'
    else:
        coding = 'utf-8'
    utf8Stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=coding)
else:
    utf8Stdout = sys.stdout

# 此处修改颜色
FMTDCIT = {
    'ERROR'   : "\033[31mERROR\033[0m",
    'INFO'    : "\033[32mINFO\033[0m",
    'DEBUG'   : "\033[1mDEBUG\033[0m",
    'WARN'    : "\033[33mWARN\033[0m",
    'WARNING' : "\033[33mWARNING\033[0m",
    'CRITICAL': "\033[35mCRITICAL\033[0m",
}

class Filter(logging.Filter):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def filter(self, record: logging.LogRecord) -> bool:
        record.levelname = FMTDCIT.get(record.levelname)
        return True

filter = Filter()

#class _utf8Stdout(object):
#
#    @classmethod
#    def write(cls, s):
#        utf8Stdout.write(s)
#        utf8Stdout.flush()
#
#    @classmethod
#    def flush(cls):
#        utf8Stdout.flush()

def Utf8Logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(utf8Stdout)
        ch.addFilter(filter)
        fmt = '[%(asctime)s][%(levelname)s][%(module)s.%(funcName)s] %(message)s'
        datefmt = '%y-%m-%d %H:%M:%S' # 普通输出
        datefmt = '\033[4;31m%Y\033[0;4m-\033[4;33m%m\033[0;4m-\033[4;32m%d\033[0;4m \033[4;36m%H\033[0;4m:\033[4;34m%M\033[0;4m:\033[4;35m%S\033[0m' # 彩色输出
        ch.setFormatter(logging.Formatter(fmt, datefmt))
        logger.addHandler(ch)
    return logger

logging.getLogger("").setLevel(logging.CRITICAL)

utf8Logger = Utf8Logger('Utf8Logger')

def SetLogLevel(level):
    utf8Logger.setLevel(getattr(logging, level.upper()))

def DisableLog():
    utf8Logger.disabled = True

def EnableLog():
    utf8Logger.disabled = False

_thisDict = globals()

for name in ('CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG'):
    _thisDict[name] = getattr(utf8Logger, name.lower())

def PRINT(*args, end='\n'):
    utf8Stdout.write(', '.join(args)+end)
    utf8Stdout.flush()

def test():
    s = input("请输入一串中文：")
    PRINT(s)
    INFO(s)
    CRITICAL(s)

if __name__ == '__main__':
    test()