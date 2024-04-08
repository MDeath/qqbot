# -*- coding: utf-8 -*-

import sys, os
from common import SGR
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
    'ERROR'   : SGR("ERROR", b4=1),
    'INFO'    : SGR("INFO", b4=2),
    'DEBUG'   : SGR("DEBUG", b4=4),
    'WARN'    : SGR("WARN", b4=3),
    'WARNING' : SGR("WARNING", b4=3),
    'CRITICAL': SGR("CRITICAL", b4=5),
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
        datefmt = f'{SGR("%y",b4=1)}-{SGR("%m",b4=3)}-{SGR("%d",b4=2)} {SGR("%H",b4=6)}:{SGR("%M",b4=4)}:{SGR("%S",b4=5)}'
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