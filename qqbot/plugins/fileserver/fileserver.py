import tornado.httpclient
import tornado.gen
import tornado.ioloop
import tornado.web
import os,re,time
from common import b64decode,b64encode

fileserver = 'http://mdie.asuscomm.com:8888'
host = ''
prot = 8888
password:str = '1064393873' # 不限时密钥
starttime = 1672531200 # 起始时间
life:int = 10800 # 链接时效 60*60
# url = http://{host}:{prot}/{time.time()-starttime+life}/{path}

def Error_Msg():
    return Head('👾')+'''
<p>لا يوجد شيء هنا </p>
<p>Здесь ничего нет.</p>
<p>Rien ici</p>
<p>这里什么也没有</p>
<p>Aquí no hay nada</p>
<p>There's nothing here</p>
'''

def Head(title):
    return f'''
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #0e0e0e;
            }}
            #noneline {{
                text-decoration: none;
                color:#000000;
            }}
            .image-container {{
                width: 100%;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #0e0e0e;
            }}
            .image {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
        </style>
    </head>'''

def onPath(path, t, imgurl):
    return f'''
    {Head(os.path.basename(path))}
    <div class="image-container"><img class="image" src="{imgurl}"/></div>
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>'''

def onImage(path, t):
    img_path = re.findall(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_\d+...', path)
    imgs = []
    for img in img_path:
        start = re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_',img).end()
        for n in range(int(img[start:-3])):
            imgs.append(f'https://i.pixiv.re/img-original/img/{img[:start]}p{n}.{img[-3:]}')
    img = '\n'.join([f'<div class="image-container"><img class="image" src="{url}"/></div>' for url in imgs])
    return f'''
    {Head(f'共计:{len(imgs)}张')}
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>'''

def onImg(path, t):
    img_path = re.findall(r'\d+-\d+...', path)
    imgs = []
    for img in img_path:
        pid, count = re.findall(r'\d+',img)
        for n in range(1, int(count)+1):
            imgs.append(f'https://pixiv.re/{pid}{"" if n==1 else f"-{n}"}.{img[-3:]}')
    img = '\n'.join([f'<div class="image-container"><img class="image" src="{url}"/></div>' for url in imgs])
    return f'''
    {Head(f'共计:{len(imgs)}张')}
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>'''

class PixivFileHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, path:str):
        print('Time:', time.strftime('\033[4;31m%Y\033[0;4m-\033[4;33m%m\033[0;4m-\033[4;32m%d\033[0;4m \033[4;36m%H\033[0;4m:\033[4;34m%M\033[0;4m:\033[4;35m%S\033[0m',time.localtime()))
        print('Path:', path)
        try:
            response = yield tornado.httpclient.AsyncHTTPClient().fetch(f'https://ip.cn/ip/{self.request.remote_ip}.html')
            location = re.search(r'<div id="tab0_address">.*?</div>',response.body.decode()).group().replace('<div id="tab0_address">','').replace('</div>','')
        except:
            location = 'Unknown'
        print('IP:', self.request.remote_ip, location)
        print('Cookies:\n', self.cookies)
        print('Headers:\n', self.request.headers)
        try:
            path = b64decode(path)
        except:
            if not path.startswith(password):
                path = None
        print('True_Path:', path)
        if not path:
            self.write(Error_Msg())
            return
        if path.startswith(password):
            path = path.replace(password,'%d'%(time.time()-starttime+life))
        t = re.search(r'\d+',path)
        t = t.group() if t else None
        print('Limit_Time:', time.strftime("\033[4;31m%Y\033[0;4m-\033[4;33m%m\033[0;4m-\033[4;32m%d\033[0;4m \033[4;36m%H\033[0;4m:\033[4;34m%M\033[0;4m:\033[4;35m%S\033[0m", time.localtime(int(t)+starttime)))
        if t and time.time()-starttime+life >= int(t) >= time.time()-starttime:
            path = path.replace(t,'')
        else:
            self.write(Error_Msg())
            return
        if os.path.isfile(path):
            imgurl = self.static_url(os.path.abspath(path).replace(os.getcwd(),'.').replace('\\','/'))
            self.write(onPath(path, t, imgurl))
        elif re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_\d+...', path):
            self.write(onImage(path, t))
        elif re.search(r'\d+-\d+...', path):
            self.write(onImg(path, t))
        else:
            self.write(Error_Msg())
            return

app = tornado.web.Application(
    [
        (r"/(.*)", PixivFileHandler),
    ],
    static_path='.'
) # 配置静态文件目录
app.listen(prot)
tornado.ioloop.IOLoop.current().start()