import soup
from common import JsonDict, DotDict, SGR, StartDaemonThread
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
import json, os, requests, time, traceback

class RequestError(Exception):
    pass

class OneBotApi():
    def __init__(self, token=None, host='localhost', hp=5700, wp=5800, **kwargs) -> None:
        self.started = None
        self.host = host
        self.hp = hp
        self.wp = wp
        self.kwargs = kwargs
        self.headers = {'Authorization':f'Bearer {token}'}
        self.Friend = lambda **kwargs:[t for t in self.List('friend') if not kwargs or all(t[k]==v for k,v in kwargs.items())]
        self.Group = lambda **kwargs:[t for t in self.List('group') if not kwargs or all(t[k]==v for k,v in kwargs.items())]
        self.Member = lambda **kwargs:[t for g in self.Group() for t in self.List('member',g.group_id) if not kwargs or all(t[k]==v for k,v in kwargs.items())]

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
                if r.get('status') != 'ok':
                    if r.get('retcode') == 9057:continue
                    ERROR(f'mode: {mode}, url: {url}, kwargs: {kwargs}, {", ".join([f"{k}: {v}" for k,v in r.items()])}')
                    return r
                return r.data
            except requests.exceptions.ConnectionError:
                ERROR('无法连接倒OneBot，请检查服务、地址、端口。')
            except RequestError as e:
                ERROR(e)
            except Exception as e:
                raise RequestError(e)

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
                    Analyst(recv)
                except Exception as e:
                    ERROR(e)
                    break

    def LoginInfo(self):
        '该接口用于获取 QQ 用户的登录号信息。'
        return self.basicsession('get','get_login_info')

    def SetProfile(self,nickname:str,company:str,email:str,college:str,personal_note:str,age:int=None,birthday:str=None):
        '''该接口用于设置 QQ 用户的个人资料信息。
    nickname		string	是	昵称
    company			string	是	公司
    email			string	是	邮箱
    college			string	是	大学
    personal_note	string	是	个人备注
    age				int32	否	年龄
    birthday		string	否	生日（格式：YYYY-MM-DD）'''
        payload = JsonDict()
        payload.nickname = nickname
        payload.company = company
        payload.email = email
        payload.college = college
        payload.personal_note = personal_note
        if age:payload.age = age
        if birthday:payload.birthday = birthday
        return self.basicsession('post','set_qq_profile',json=payload)

    def List(self, mode:str, gid:int=None, **kwargs):
        '''该接口用于获取联系人列表。
    mode	string	是	获取对象类型：unfriend|friend|group|member
	gid		int		否	群ID'''
        mode = mode.lower()
        payload = JsonDict()
        if mode == 'unfriend':url = 'get_unidirectional_friend_list'
        elif mode == 'friend':url = 'get_friend_list'
        elif mode == 'group':
            url = 'get_group_list'
            payload.no_cache = True
        elif mode == 'member':
            url = 'get_group_member_list'
            payload.group_id = int(gid)
        return self.basicsession('post',url,json=payload)

    def Info(self, mode:str, target:int, gid:int=None):
        '''获取联系人信息。
    mode	string	是	获取对象类型：unfriend|group|honor|member
	target	int		是	获取目标ID
	gid		int		否	群ID'''
        mode = mode.lower()
        payload = JsonDict()
        if mode == 'unfriend':
            url = 'get_stranger_info'
            payload.user_id = int(target)
        elif mode == 'group':
            url = 'get_group_info'
            payload.group_id = int(target)
        elif mode == 'honor':
            url = 'get_group_honor_info'
            payload.group_id = int(target)
        elif mode == 'member':
            url = 'get_group_member_info'
            payload.user_id = int(target)
            payload.group_id = int(gid)
        return self.basicsession('post', url, json=payload)

    def SystemMsg(self, mode:str):
        '''该接口用于获取请求系统消息。
    mode	string	是	请求类型：friend|group'''
        mode = mode.lower()
        return self.basicsession('get',f'get_{mode}_system_msg')

    def HistoryMsg(self, mode:str, target:int, start:int=0, count:int=0):
        '''获取历史消息
    start	int	是	由此消息ID往前'''
        mode = mode.lower()
        payload = JsonDict()
        if mode == 'friend':
            payload.message_type = 'private'
            payload.user_id = target
        else:
            payload.message_type = 'group'
            payload.group_id = target
        if start:payload.message_seq = start
        if count:payload.count = count
        return self.basicsession('post','get_history_msg',json=payload)

    def GetMsg(self, id:int):
        '''获取消息
    id	int	是	消息ID'''
        obj = self.basicsession('post','get_msg',json={'message_id':id})
        for msg in obj.message: # 消息链处理
            if 'type' in msg.data:msg.data.data_type = msg.data.pop('type') # data内有type转成data_type
            msg.update(msg.pop('data')) # 把data往上提取一层
        return obj

    def GetForward(self, id):
        '''获取合并转发内容
    id	string	是	消息资源ID（卡片消息里面的resId）'''
        return self.basicsession('post','get_forward_msg',json={'id':id})

    def SendMsg(self, mode:str, target:int, *message:object|list, reply:int=0, recall:int=0):
        '''该接口用于发送消息。
    '''
        mode = mode.lower()
        payload = JsonDict({'user_id' if mode == 'friend' else 'group_id':target})
        message = [JsonDict({'type':msg.pop('type'), 'data':msg}) for msg in [JsonDict(msg.copy()) for msg in list(message) + ([soup.Reply(reply)] if reply else [])]]
        if any([msg.type=='node' for msg in message]):
            url = 'send_private_forward_msg' if mode == 'friend' else 'send_group_forward_msg'
            for node in message:
                if 'content' in node.data:node.data.content = [{'type':msg.pop('type'),'data':msg} for msg in [msg.copy() for msg in node.data.content]]
            payload.messages = message
        else:
            url = 'send_msg'
            payload.message_type = 'private' if mode == 'friend' else 'group'
            if recall:payload.recall_duration = recall
            for msg in message:
                if 'data_type' in msg.data:msg.data.type = msg.data.pop('data_type')
            payload.message = message
        data = self.basicsession('post',url,json=payload)
        if mode=="friend":
            target = self.Friend(user_id=target)[0]
            INFO(f'发到好友{SGR(target.nickname,b4=11)}[{SGR(target.remark,b4=11)}({SGR(target.user_id,b4=1)})]{(reply and "回复("+SGR(reply,b4=2)+")") or ""}消息({SGR(data.message_id, b4=12) if "message_id" in data else SGR(data.retcode, b4=11)}):\n{str(message)}')
        elif mode=="group":
            target = self.Group(group_id=target)[0]
            INFO(f'发到群{SGR(target.group_name,b4=14)}({SGR(target.group_id,b4=4)}){(reply and "回复("+SGR(reply,b4=2)+")") or ""}消息({SGR(data.message_id, b4=12) if "message_id" in data else SGR(data.retcode, b4=11)}):\n{str(message)}')
        return data

    def Recall(self, id:int):
        '''该接口用于撤回消息。
    id	int	是	消息ID'''
        return self.basicsession('post','delete_msg',json={'message_id':id})

    def Reaction(self, gid, message_id, face_id, is_add=True):
        return self.basicsession('post','set_group_reaction',json={"group_id": gid,"message_id": message_id,"code": str(face_id),"is_add": is_add})

    def GetImage(self, file:str):
        return self.basicsession('post','get_image',json={'file':file})

    def GetRecord(self, file:str, out:str='mp3'):
        return self.basicsession('post','get_record',json={'file':file,'out_format':out})

    def GetFile(self, file:str, type:str='base64'):
        return self.basicsession('post','get_file',json={'file':file,'file_type':type})

    def request_response(self, Request:dict, approve:bool=False, re:str=None):
        payload = JsonDict()
        payload.flag = Request.flag
        payload.approve = True if approve else False
        if Request.request_type == "friend":
            if re:payload.remark = re
        else:
            payload.sub_type = Request.sub_type
            if re:payload.reason = re
        print(payload)
        return self.basicsession('post',f'set_{"friend" if Request.request_type == "friend" else "group"}_add_request', json=payload)

    def SetGroupName(self, gid:int, name:str):
        return self.basicsession('post','set_group_name', json={'group_id':gid, 'group_name':name})

    def SetGroupAdmin(self, gid:int, uid:int, enable:True):
        return self.basicsession('post','set_group_admin', json={'group_id':gid, 'user_id':uid, 'enable':enable})

    def SetGroupCard(self, gid:int, uid:int, card:str=None):
        payload = JsonDict({'group_id':gid, 'user_id':uid})
        if card:payload.card = card
        return self.basicsession('post','set_group_admin', json=payload)

host = 'localhost'
hp = 5700
wp = 5800
token = '0123456789'
if __name__ == '__main__':
    bot = OneBotApi(token,host,hp,wp)
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