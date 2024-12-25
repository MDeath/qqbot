import tornado.httpclient
import tornado.gen
import tornado.ioloop
import tornado.web
import os,re,time,traceback,mimetypes,urllib.parse
from qqbotcls import bot
from common import b64dec,b64enc,DotDict,jsonload,jsonloads,jsondump,StartDaemonThread,search
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
    'https://img.mdie.top'
]

def get_host():
    hosts.insert(0,hosts.pop())
    return hosts[0]

log_title = '访问时间,限制时间,Cookies,Headers,路径,真实路径,编码,超时,正常\n'

def log_write(*arge):
    if not os.path.exists(f'logs/fileserver_{time.strftime("%Y-%m")}.csv'):
        with open(f'logs/fileserver_{time.strftime("%Y-%m")}.csv', 'w', encoding='UTF-8') as f:f.write(log_title)
    with open(f'logs/fileserver_{time.strftime("%Y-%m")}.csv', 'a', encoding='UTF-8') as f:f.write(','.join([str(i).replace('\n',r'\n').replace('\r',r'\r').replace(',',';') for i in arge])+'\n')

user_illusts_path = r"/Media/Picture/Pixiv/user_illusts" # 相对位置
fileserver = 'https://pixiv.mdie.top'
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

def Image_box(num, original, medium=None):
    return f'''\
    <div id="img{num}" class="image-container">
        <div id="btn1" class="btn" onclick="loadImage('img{num}', '{original}')">
            <img class="image" src="{medium or original}" alt="点击加载">
        </div>
    </div>'''

def onPath(path, t, imgurl):
    return f'''\
{Head(os.path.basename(path))}
<div class="image-container"><img class="image" src="{imgurl}" alt="{imgurl}"/></div>
<h1 style="text-align:center;">
    <a href="{fileserver}/{b64enc('%d%s'%(int(t)+life/2, path))}" id="noneline">
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
            imgs.append( 
                f'{get_host()}/img-original/img/{start}p{num}.{end}'
            )
    img = '\n'.join([f'<div class="image-container"><a href="{img}"><img class="image" src="{img}" alt="重新加载"/></a></div>' for img in imgs])
    return f'''\
<!doctype html>
<html>
{Head(f'共计:{len(imgs)}张')}
<body>
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64enc('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>
</body>
</html>'''

def onIllusts(img_path, t, path, medium=False):
    imgs = []
    for pid in img_path:
        for illust in bot.illusts:
            if pid == illust['pid']:
                break
        else:
            illust = bot.pixiv.illust_detail(pid)
            if 'error' in illust:continue
            if not (illust.illust.title or illust.illust.user.name):continue
            illust = {'uid':illust.illust.user.id,'pid':pid,'type':illust.illust.type,'count':illust.illust.page_count,'medium':illust.illust.image_urls.medium,'original':illust.illust.meta_single_page.original_image_url if illust.illust.page_count == 1 else illust.illust.meta_pages[0].image_urls.original}
            bot.illusts.append(illust)
        for n in range(illust['count']):
            if illust['type'] == 'ugoira':
                for u in os.listdir(user_illusts_path):
                    if str(illust['uid']) in u:
                        for i in os.listdir(os.path.join(user_illusts_path,u)):
                            if str(illust['pid']) in i:
                                imgs.append([os.path.join(user_illusts_path,u,i).replace('\\','/').replace('#','%23')]*2)
                                break
                        break
                else:
                    imgs.append([
                        illust['original'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host()),
                        illust['medium'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host())
                    ])
            else:
                imgs.append([
                    illust['original'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host()),
                    illust['medium'].replace('_p0',f"_p{n}").replace('https://i.pximg.net',get_host())
                ])
    img = '\n'.join([Image_box(num, imgs[num][0], imgs[num][1] if medium else None) for num in range(len(imgs))])
    bot.illusts = bot.illusts[-1000:]
    return f'''\
<!doctype html>
<html>
{Head(f'共计:{len(imgs)}张')}
<body>
    {img}
    <h1 style="text-align:center;">
        <a href="{fileserver}/{b64enc('%d%s'%(int(t)+life/2, path))}" id="noneline">
            过期时间：{time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(t)+starttime))}
        </a>
    </h1>
</body>
</html>'''

class PixivFileHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, path:str):
        if any([key in path for key in ["user-profile/img","img-original/img","img-master/img"]]):
            INFO(path)
            # 构建代理 URL
            url = f"https://i.pximg.net{path}"
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
        elif path.startswith('/lolicon'):
            response = yield tornado.httpclient.AsyncHTTPClient().fetch(f'https://api.lolicon.app/setu/v2?{self.request.query}' if self.request.query else 'https://api.lolicon.app/setu/v2')
            imgs = '\n'.join([f'<div class="image-container"><img class="image" src="{url["urls"]["original"]}" alt="{url["urls"]["original"]}"/></div>' for url in jsonloads(response.body.decode())['data']])
            self.write(f"{Head('')}{imgs}")
            return
        elif path.startswith(user_illusts_path):
            content_type, _ = mimetypes.guess_type(path) # 使用 mimetypes 模块自动推断文件类型
            if not content_type:content_type = "application/octet-stream" # 如果无法确定文件类型，则默认为 application/octet-stream
            self.set_header("Content-Type", content_type)# 设置响应头 Content-Type
            with open(path,'rb') as f:return self.write(f.read())
        path = path[1:] # 移除 /
        now = time.localtime()
        try: # 尝试解码
            true_path = b64dec(path)
            enc = True
        except:
            true_path = path
            enc = False
        if true_path.startswith(password): # 密钥开头
            t = '%d'%(time.time()-starttime+life) # 生成过期时间戳
            medium = False
        else:
            medium = True
            t = re.search(r'\d+',true_path) 
            t = t.group() if t else None # 获取过期时间戳
        timeout = not (t and time.time()-starttime+life >= int(t) >= time.time()-starttime)
        true_path = true_path.replace(password,'').replace(t or '','')
        # try: # 尝试获取位置信息
        #     response = yield tornado.httpclient.AsyncHTTPClient().fetch(f'https://ip.cn/api/index?{urllib.parse.urlencode({"ip":self.request.remote_ip,"type":1})}')
        #     location = tornado.escape.json_decode(response.body)
        # except:
        #     ERROR(traceback.format_exc())
        #     location = 'Unknown'
# IP:{location['ip']}\t{location['address']}
# location['ip'],location['address'],
        INFO(f'''
Limit_Time:{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(t)+starttime)) if t else time.strftime("%Y-%m-%d %H:%M:%S",now)}
Path:{path}
True_Path:{true_path}
Cookies:-   +   -   +   -   +
{self.cookies}
Headers:-   +   -   +   -   +
{self.request.headers}
Encode:{enc}\ttimeout:{timeout}\tnormal:{enc and not timeout}''')
        log_write(time.strftime('%Y-%m-%d %H:%M:%S',now),time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(int(t)+starttime))if t else time.strftime('%Y-%m-%d %H:%M:%S',now),dict(self.cookies),dict(self.request.headers),path,true_path,enc,timeout,enc and not timeout)
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
                self.write(onIllusts([int(pid,16) for pid in re.findall(r'x([0-9a-fA-F]+)', true_path)], t, true_path, medium))
            else:
                self.write(Error_Msg())
                return
        except:traceback.print_exc()

app = tornado.web.Application(
    [
        (r"(.*)", PixivFileHandler),
    ],
    static_path='.' # 配置静态文件目录
)

def onPlug(bot):
    if not hasattr(bot,'server'):bot.server = app.listen(prot)
    if not hasattr(bot,'illusts'):
        try:
            if os.path.exists(bot.conf.Config('illusts.json')):
                with open(bot.conf.Config('illusts.json'), 'r', encoding='utf-8') as f:bot.illusts = jsonload(f)
            else:raise
        except:bot.illusts = []
    StartDaemonThread(tornado.ioloop.IOLoop.current().start)

def onUnplug(bot):
    tornado.ioloop.IOLoop.current().stop()
    if hasattr(bot,'server'):bot.server.stop()
    del bot.server

def onInterval(bot): # 保存illusts记录
    with open(bot.conf.Config('illusts.json'), 'w', encoding='utf-8') as f:jsondump(bot.illusts, f, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    app.listen(prot)
    bot.server = app.listen(prot)
    illusts = []
    tornado.ioloop.IOLoop.current().start()