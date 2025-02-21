import soup
from common import JsonDict, DotDict, SGR, StartDaemonThread
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
import json, os, requests, time, traceback, typing

class RequestError(Exception):
    pass

class Language():
    def __init__(self, token=None, host='localhost', hp=5700, wp=5800, **kwargs) -> None:
        self.started = False
        self.host = host
        self.hp = hp
        self.wp = wp
        self.kwargs = kwargs
        self.headers = {'Authorization':f'Bearer {token}'}
        self.Friend = lambda **kwargs:[t for t in self.List('friend') if not kwargs or all(t[k]==v for k,v in kwargs.items())]
        self.Group = lambda **kwargs:[t for t in self.List('group') if not kwargs or all(t[k]==v for k,v in kwargs.items())]
        self.Member = lambda **kwargs:[t for g in self.Group() for t in self.List('member',g.group_id) if not kwargs or all(t[k]==v for k,v in kwargs.items())]

    ErrorCode = None
    ErrorTime = None

    def basicsession(self, mode, url, **kwargs):
        kw = kwargs
        kw.update(self.kwargs)
        while True:
            if not self.started:continue
            try:
                DEBUG(f'url:http://{self.host}:{self.hp}/{url} kw:{kw}')
                response = getattr(requests, mode)(f'http://{self.host}:{self.hp}/{url}',headers=self.headers , **kw)
                r = DotDict(response.text)
                if response.status_code != 200:raise RequestError(f'status_code: {response.status_code}')
                break
            except requests.exceptions.ConnectionError:
                ERROR('无法连接倒OneBot，请检查服务、地址、端口。')
            except RequestError as e:
                ERROR(e)
            except Exception as e:
                raise RequestError(e)
        if (hasattr(r, 'status') and r.status != 'ok') or (hasattr(r,'retcode') and r.retcode != 0):
            ERROR(f'mode: {mode}, url: {url}, kwargs: {kwargs}, {", ".join([f"{k}: {v}" for k,v in r.items()])}')
            return r
        return r.data

### 消息与事件上报 ###
    def pollForever(self, Analyst): # WS Adapter
        import websocket
        while True:
            try:
                self.ws = websocket.create_connection(f'ws://{self.host}:{self.wp}', header=self.headers, timeout=60)
                recv = self.ws.recv()
                if not recv:raise
                recv = DotDict(recv)
            except:
                if self.started:
                    ERROR('qsession.Poll 方法出错请检查连接配置', exc_info=True)
                    self.started = False
                time.sleep(15)
                continue
            INFO(f'qq:{recv.self_id} 链接成功')
            self.qq = recv.self_id
            self.started = True
            while self.started:
                try:
                    recv = DotDict(self.ws.recv())
                    if recv.post_type == 'meta_event':
                        DEBUG(f'qq.status:{recv.status["qq.status"]}')
                        continue
                    StartDaemonThread(Analyst, recv)
                except Exception as e:
                    ERROR(e)
                    break
    
    # Ability 能力
    def can_send_image(self) -> bool:
        '''检查是否可以发送图片'''
        return self.basicsession('get','can_send_image').yes

    def can_send_record(self) -> bool:
        '''检查是否可以发送语音'''
        return self.basicsession('get','can_send_record').yes

    def upload_image(self, file:str) -> True|JsonDict:
        '''
        上传图片
        ### 请求参数
        |名称|位置|类型|必选|说明|
        |---|---|---|---|---|
        |file|body|string| 是 |file 链接, 支持 http/https/file/base64|
        ### 返回数据结构
        |名称|类型|必选|约束|中文名|说明|
        |---|---|---|---|---|---|
        |» data|string|true|none||文件 Url|
        '''
        return self.basicsession('post','upload_image',json=file)

    # File 文件
    def get_private_file_url(self):
        '''
        获取私聊文件资源链接
        ### 请求参数
        |名称|位置|类型|必选|说明|
        |---|---|---|---|---|
        |» user_id|body|integer| 是 |用户 Uin，接收文件用户的Uin|
        |» file_id|body|string| 是 |文件 ID|
        |» file_hash|body|string| 否 |文件 Hash|
        ### 返回数据结构
        |名称|类型|必选|约束|中文名|说明|
        |---|---|---|---|---|---|
        |»» url|string|true|none||文件下载链接|
        '''
    # def get_group_file_url(self):
    # def get_group_root_files(self):
    # def get_group_files_by_folder(self):
    # def move_group_file(self):
    # def delete_group_file(self):
    # def create_group_file_folder(self):
    # def delete_group_file_folder(self):
    # def rename_group_file_folder(self):
    # def upload_group_file(self):
    # def upload_private_file(self):

    # # Generic 通用(self):
    # def fetch_custom_face(self):
    # def fetch_mface_key(self):
    # def .join_friend_emoji_chain(self):
    # def get_ai_characters(self):
    # def get_cookies(self):
    # def get_credentials(self):
    # def get_csrf_token(self):
    # def .join_group_emoji_chain(self):
    # def ocr_image(self):
    # def set_qq_avatar(self):
    # def send_like(self):
    # def set_restart(self):
    # def delete_friend(self):
    # def get_rkey(self):

    # # Request 请求(self):
    # def set_friend_add_request(self):
    # def set_group_add_request(self):


if __name__ == '__main__':
    protocol = 'http'
    host = 'mdie.top'
    hp = 9700
    wp = 9800
    token = '1064393873.lx'
    bot = Language(token,host,hp,wp)
    StartDaemonThread(bot.pollForever,INFO)
    while True:
        try:
            commad = input('>')
            if not commad:pass
            elif commad.lower() in ['?','help']:
                [print(f) for f in dir(bot) if not f.startswith('_')]
            else:
                print(eval(commad))
        except KeyboardInterrupt:
            exit()
        except:
            traceback.print_exc()