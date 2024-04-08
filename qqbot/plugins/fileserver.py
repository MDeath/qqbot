import tornado.httpclient
import tornado.gen
import tornado.ioloop
import tornado.web
import os,re,time,json,platform,traceback
from qqbotcls import bot
from common import b64decode,b64encode,DotDict,jsondumps,StartDaemonThread
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING

config = {
    'REFRESH_TOKEN':'',
    'USERNAME':'',
    'PASSWORD':''
}

# 图片代理
hosts = [
    # 'https://i.pixiv.cat',
    'https://i.pixiv.re',
    'https://i.pixiv.nl',
    # 'https://i-cf.pximg.net',
    # 'http://mdie.asuscomm.com:8888',
]
def get_host():
    hosts.insert(0,hosts.pop())
    return hosts[0]

log_title = '访问时间,限制时间,IP,位置,Cookies,Headers,路径,真实路径,编码,超时,正常\n'

def log_write(*arge):
    if not os.path.exists(f'fileserver_{time.strftime("%Y-%m")}.csv'):
        with open(f'fileserver_{time.strftime("%Y-%m")}.csv', 'w', encoding='GBK') as f:f.write(log_title)
    with open(f'fileserver_{time.strftime("%Y-%m")}.csv', 'a', encoding='GBK') as f:f.write(','.join([str(i).replace('\n',r'\n').replace('\r',r'\r').replace(',',';') for i in arge])+'\n')

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
    return f'''\
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>{title}</title>
    <style>
        html,
        body {{
            margin: 0;
            padding: 0;
            background-color: #222222;
        }}

        .btn {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 98%;
            height: 98%;
            border: 5px dashed #FE82A5;
            color: #FE82A5;
            font-size: 5em;
            margin-top: 20px;
            cursor: pointer;
        }}

        #noneline {{
            text-decoration: none;
            color: #111111;
        }}

        .image-container {{
            width: 100%;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            background-color: #222222;
        }}

        .image {{
            max-width: 100%;
            max-height: 100vh;
            object-fit: contain;
        }}
    </style>
</head>

<script>
    function loadImage(imgId, imgUrl) {{
        document.getElementById(imgId).innerHTML = `<a href="${{imgUrl}}"><img class="image" src="${{imgUrl}}" alt="重新加载"/></a>`;
    }}
</script>
'''

def Image_box(num, medium, original):
    return f'''\
    <div id="img{num}" class="image-container">
        <div id="btn1" class="btn"
            onclick="loadImage('img{num}', '{original}')">
            <img class="image"
                src="{medium}"
                alt="点击加载">
        </div>
    </div>'''

def onPath(path, t, imgurl):
    return f'''
{Head(os.path.basename(path))}
<div class="image-container"><img class="image" src="{imgurl}" alt="{imgurl}"/></div>
<h1 style="text-align:center;">
    <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
        过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
    </a>
</h1>'''

def onIllustPath(path, t):
    img_path = list(zip(
        re.findall(r'(\d+/\d+/\d+/\d+/\d+/\d+/\d+_)\d+...', path), 
        re.findall(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_(\d+)...', path), 
        re.findall(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_\d+(...)', path)
    ))
    imgs = []
    for start, count, end in img_path:
        for num in range(int(count)):
            imgs.append([
                f'{get_host()}/c/540x540_70/img-master/img/{start}p{num}_master1200.jpg', 
                f'{get_host()}/img-original/img/{start}p{num}.{end}'
            ])
    img = '\n'.join([Image_box(num, imgs[num][0], imgs[num][1]) for num in range(len(imgs))])
    return f'''\
<!doctype html>
<html>
{Head(f'共计:{len(imgs)}张')}
<body>
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>
</body>
</html>'''

def onIllusts(img_path, t, path):
    imgs = []
    global illusts
    for pid in img_path:
        for illust in illusts:
            if pid == illust['pid']:
                break
        else:
            illust = bot.pixiv.illust_detail(pid)
            if 'error' in illust:continue
            if not (illust.illust.title or illust.illust.user.name):continue
            illust = {'pid':pid,'count':illust.illust.page_count,'medium':illust.illust.image_urls.medium,'original':illust.illust.meta_single_page.original_image_url if illust.illust.page_count == 1 else illust.illust.meta_pages[0].image_urls.original}
            illusts.append(illust)
        for n in range(illust['count']):
            imgs.append([
                illust['medium'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host()),
                illust['original'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host())
            ])
    img = '\n'.join([Image_box(num, imgs[num][0], imgs[num][1]) for num in range(len(imgs))])
    illusts = illusts[-1000:]
    return f'''\
<!doctype html>
<html>
{Head(f'共计:{len(imgs)}张')}
<body>
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64encode('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>
</body>
</html>'''

class PixivFileHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, path:str):
        if any([key in path for key in ["user-profile/img","img-original/img","img-master/img"]]):
            # 构建代理 URL
            url = f"https://i.pximg.net/{path}"
            # 使用 Tornado 的 HTTP 客户端发送请求
            try:
                response = yield tornado.httpclient.AsyncHTTPClient().fetch(url, headers={"Referer": "https://app-api.pixiv.net/"})
                # 设置原始响应的状态码
                self.set_status(response.code)
                self.set_header('Content-Type', 'image/png')
                # 将来自 i.pximg.net 的响应原样返回
                self.write(response.body)
            except tornado.httpclient.HTTPError as e:
                if e.response:
                    self.set_status(e.response.code)
                    self.write(e.response.body)
                else:
                    self.set_status(500)
                    self.write("Internal server error")
            except Exception as e:
                self.set_status(500)
                self.write("server error")
            return
        elif path.startswith('lolicon'):
            response = yield tornado.httpclient.AsyncHTTPClient().fetch(f'https://api.lolicon.app/setu/v2?{self.request.query}' if self.request.query else 'https://api.lolicon.app/setu/v2')
            imgs = '\n'.join([f'<div class="image-container"><img class="image" src="{url["urls"]["original"]}" alt="{url["urls"]["original"]}"/></div>' for url in json.loads(response.body.decode())['data']])
            self.write(f"{Head('')}{imgs}")
            return
        now = time.localtime()
        try: # 尝试解码
            true_path = b64decode(path)
            enc = True
        except:
            true_path = path
            enc = False
        if true_path.startswith(password): # 密钥开头
            t = '%d'%(time.time()-starttime+life) # 生成过期时间戳
        else:
            t = re.search(r'\d+',true_path) 
            t = t.group() if t else None # 获取过期时间戳
        timeout = not (t and time.time()-starttime+life >= int(t) >= time.time()-starttime)
        true_path = true_path.replace(password,'').replace(t or '','')
        try: # 尝试获取位置信息
            response = yield tornado.httpclient.AsyncHTTPClient().fetch(f'https://ip.cn/ip/{self.request.remote_ip}.html')
            location = re.search(r'<div id="tab0_address">.*?</div>',response.body.decode()).group().replace('<div id="tab0_address">','').replace('</div>','')
        except:
            location = 'Unknown'
        INFO(f'''
Limit_Time:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(t)+starttime)) if t else time.strftime("%Y-%m-%d %H:%M:%S",now)}
Path:{path}
True_Path:{true_path}
IP:{self.request.remote_ip}\t{location}
Cookies:-   +   -   +   -   +
{self.cookies}
Headers:-   +   -   +   -   +
{self.request.headers}
Encode:{enc}\ttimeout:{timeout}\tnormal:{enc and not timeout}''')
        log_write(time.strftime('%Y-%m-%d %H:%M:%S',now),time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(t)+starttime))if t else time.strftime('%Y-%m-%d %H:%M:%S',now),self.request.remote_ip,location,dict(self.cookies),dict(self.request.headers),path,true_path,enc,timeout,enc and not timeout)
        try:
            if timeout:
                self.write(Error_Msg())
                return
            if os.path.isfile(true_path):
                imgurl = self.static_url(os.path.abspath(true_path).replace(os.getcwd(),'.').replace('\\','/'))
                self.write(onPath(true_path, t, imgurl))
            elif re.search(r'\d+/\d+/\d+/\d+/\d+/\d+/\d+_\d+...', true_path):
                self.write(onIllustPath(true_path, t))
            elif re.search(r'x[0-9a-fA-F]+', true_path):
                self.write(onIllusts([int(pid,16) for pid in re.findall(r'x([0-9a-fA-F]+)', true_path)], t, true_path))
            else:
                self.write(Error_Msg())
                return
        except:traceback.print_exc()

app = tornado.web.Application(
    [
        (r"/(.*)", PixivFileHandler),
    ],
    static_path='.' # 配置静态文件目录
)

def onPlug(bot):
    if not hasattr(bot,'server'):bot.server = app.listen(prot)
    global illusts
    illusts = []
    StartDaemonThread(tornado.ioloop.IOLoop.current().start)

def onUnplug(bot):
    tornado.ioloop.IOLoop.current().stop()
    if hasattr(bot,'server'):bot.server.stop()
    del bot.server

if __name__ == '__main__':
    app.listen(prot)
    bot.server = app.listen(prot)
    illusts = []
    tornado.ioloop.IOLoop.current().start()
