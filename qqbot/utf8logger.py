# -*- coding: utf-8 -*-

import logging.handlers
import sys, os, logging
from common import SGR
p = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if p not in sys.path:
    sys.path.insert(0, p)
if not os.path.exists('logs'):
    os.mkdir('logs')

# 此处修改等级颜色
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

def Utf8Logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = '[%(asctime)s][%(levelname)s][%(module)s.%(funcName)s] %(message)s'
        if sys.argv[-1] == '--subprocessCall':lf = logging.handlers.TimedRotatingFileHandler('logs/bot.log','D',encoding='utf-8')
        else: lf = logging.FileHandler('logs/main.log','a',encoding='utf-8')
        datefmt = f'{SGR("%y",b4=1)}-{SGR("%m",b4=3)}-{SGR("%d",b4=2)} {SGR("%H",b4=6)}:{SGR("%M",b4=4)}:{SGR("%S",b4=5)}'
        lf.setFormatter(logging.Formatter(fmt, datefmt))
        logger.addHandler(lf)
        ch = logging.StreamHandler()
        ch.addFilter(Filter())
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
    sys.stderr.write(', '.join(args)+end)
    sys.stderr.flush()

def test():
    SetLogLevel('DEBUG')
    s = input("请输入一串中文：")
    DEBUG(s)
    PRINT(s)
    INFO(s)
    CRITICAL(s)

if __name__ == '__main__':
    test()