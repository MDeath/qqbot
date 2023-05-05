import tornado.ioloop
import tornado.web

from .fileserver import PixivFileHandler

fileserver = 'http://mdie.asuscomm.com:8888'
host = ''
prot = 8888
password:str = '1064393873' # 不限时密钥
starttime = 1672531200 # 起始时间
life:int = 10800 # 链接时效 60*60
# url = http://{host}:{prot}/{time.time()-starttime+life}/{path}

host: str = 'localhost'
port: int = 8190

app = tornado.web.Application(
    [
        (r"/(.*)", PixivFileHandler),
    ],
    static_path='.'
) # 配置静态文件目录
app.listen(prot)
tornado.ioloop.IOLoop.current().start()