# -*- coding: utf-8 -*-

from common import parse_json
from utf8logger import INFO, ERROR, WARNING
import json, requests

def Get(*args, **kwargs):
        while True:
            try:
                return requests.get(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                ERROR('无法连接倒Mirai，请检查服务、地址、端口。')
            except:
                raise RequestError

def Post(*args, **kwargs):
        while True:
            try:
                return requests.post(*args, **kwargs)
            except requests.exceptions.ConnectionError:
                ERROR('无法连接倒Mirai，请检查服务、地址、端口。')
            except:
                raise RequestError

class RequestError(Exception):
    pass

class MiraiApi():
    def __init__(self, qq, verifyKey, host='localhost', port=8080, session=None) -> None:
        self.started = False
        self.host=host
        self.port=port
        self.qq = qq
        self.verifyKey = verifyKey
        if session:self.session = session
        else:self.Verify()

    def ErrorCode(self, code):
        if code == 1:
            ERROR('错误的verify key')
            self.verifyKey = input('verifyKey:')
        elif code == 2:
            ERROR('指定的Bot不存在')
            self.qq = int(input('qq:'))
        elif code == 3:
            WARNING('Session失效或不存在')
            self.Verify()
            return 1
        elif code == 4:
            WARNING('Session未认证(未激活)')
            self.Bind()
            return 1
        elif code == 5:
            WARNING('发送消息目标不存在(指定对象不存在)')
        elif code == 6:
            WARNING('指定文件不存在，出现于发送本地图片')
        elif code == 10:
            WARNING('无操作权限，指Bot没有对应操作的限权')
        elif code == 20:
            WARNING('Bot被禁言，指Bot当前无法向指定群发送消息')
        elif code == 30:
            WARNING('消息过长')
        elif code == 400:
            WARNING('错误的访问，如参数错误等')
        return 0

    def basicsession(self,mode,url,**kwargs):
        r = parse_json(mode(f'http://{self.host}:{self.port}/{url}', **kwargs).text)
        if hasattr(r, 'code') and r.code:
            self.ErrorCode(r.code)
            return
        if hasattr(r, 'data'):
            return r.data
        elif hasattr(r, 'messageId'):
            return r.messageId
        else:
            return r

    def Verify(self): # 认证
        self.started = False
        payload = {"verifyKey": self.verifyKey}
        r = self.basicsession(Post, 'verify', data=json.dumps(payload))
        if r:
            self.session = r.session
            INFO('认证成功')
            self.Bind()
        else:
            self.Verify()

    def Bind(self): # 绑定
        payload = {
            "sessionKey": self.session,
            "qq": self.qq
        }
        r = self.basicsession(Post, 'bind', data=json.dumps(payload))
        if r:
            INFO('绑定成功')
            self.started = True
        else:
            self.Bind()

### 消息与事件 ###

    def GetMessage(self) -> list: # 获取消息
        payload = {'sessionKey':self.session}
        payload['count'] = 10
        return self.basicsession(Get, f'fetchMessage', params=payload)

    def MessageFromId(self, messageID:int) -> dict: # 通过MessageID获取消息
        payload = {'sessionKey':self.session,'id':messageID}
        return self.basicsession(Get, 'messageFromId', params=payload)

    def SendMessage(self, Type:str, target:int, *message:dict, quote:int=None) -> int: # 发给好友、群、临时消息，返回消息ID
        r'''form = Friend, Group, Temp
        Group and Friend: target = target
        Temp: qq = qqID, or group = groupID

        quote is messageID
        message is messagelist
        '''
        if Type not in ['Friend', 'Group', 'Temp']:
            raise RequestError
        payload = {'sessionKey':self.session}
        if Type != 'Temp':
            payload['target'] = target
        elif Type == 'Temp':
            payload['qq'] = target
            payload['group'] = target
        payload['messageChain'] = [msg for msg in message]
        if quote:
            payload['quote'] = quote
        INFO(f'发到 {Type} {target}:{(quote and "回复消息 "+str(quote)+" ") or " "}{message}')
        Quote = self.basicsession(Post, f'send{Type}Message', data=json.dumps(payload))
        if Quote:return Quote
        else:WARNING(f'发到 {Type} {target} 发送失败')

    def Nudge(self, type:str, target:int, id:int) -> None: # 戳一戳
        r'''kind = Friend, Group, Stranger
        subject = qqID, groupID
        target = qqID, memberID
        '''
        if type not in ['Friend', 'Group', 'Stranger']:raise RequestError
        payload = {'sessionKey':self.session}
        payload['target'] = id
        payload['subject'] = target
        payload['kind'] = type
        return self.basicsession(Post, 'sendNudge', data=json.dumps(payload))

    def Recall(self, messageID:int) -> None: # 撤回消息
        payload = {'sessionKey':self.session}
        payload['target'] = messageID
        return self.basicsession(Post, '/recall', data=json.dumps(payload))

    def Event_response(self, even, operate:int=0, msg:str=''):
        payload = {'sessionKey':self.session}
        payload['eventId'] = even.eventId
        payload['fromId'] = even.fromId
        payload['groupId'] = even.groupId
        payload['operate'] = operate
        payload['message'] = msg
        type = even.type[0].lower() + even.type[1:]
        self.basicsession(Post, f'resp/{type}', data=json.dumps(payload))

### 联系人操作 ###

    def List(self, type:str, groupID:int=None) -> list: # 获取好友、群、成员列表
        r'type = Friend , Group , Member'
        if type not in ['Friend', 'Group', 'Member']:raise RequestError
        payload = {'sessionKey':self.session}
        if type == 'member':payload['target'] = groupID
        return self.basicsession(Get, f'{type.lower()}List', params=payload)

    def Profile(self, form:str, target:int=None, memberID:int=None) -> dict: # 获取bot、好友、成员资料
        r'''form = bot, friend, member
        friend: targer = friendID
        member: targer = groupID, memberID = memberID
        '''
        if form not in ['bot', 'friend', 'member']:raise RequestError
        payload = {'sessionKey':self.session}
        if form != 'bot':
            payload['target'] = target
        if form == 'member':
            payload['memberId'] = memberID
        return self.basicsession(Get, f'{form}Profile', params=payload)

    def DeleteFriend(self, target:int): # 删除好友
        payload = {'sessionKey':self.session}
        payload['target'] = target
        return self.basicsession(Post, 'deleteFriend', data=json.dumps(payload))

### 群管理 ###

    def Mute(self, target:int, memberID:int, time:int=0, un:bool=False): # 禁言
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        payload['time'] = time
        un = (un and 'un') or ''
        return self.basicsession(Post, f'{un}mute', data=json.dumps(payload))

    def kick(self, target:int, memberID:int, msg:str=''): # 移除成员
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        payload['msg'] = msg
        return self.basicsession(Post, 'kick', data=json.dumps(payload))

    def quit(self, target:int): # 退群
        payload = {'sessionKey':self.session}
        payload['target'] = target
        return self.basicsession(Post, 'quit', data=json.dumps(payload))

    def MuteAll(self, target:int, un:bool=False): # 全体禁言
        payload = {'sessionKey':self.session}
        payload['target'] = target
        un = (un and 'un') or ''
        return self.basicsession(Post, f'{un}muteAll', data=json.dumps(payload))

    def SetEssence(self, messageID:int): # 设置精华消息
        payload = {'sessionKey':self.session}
        payload['messageId'] = messageID
        return self.basicsession(Post, 'setEssence', data=json.dumps(payload))

    def GroupConfig(self, mode, target:int, name:str=None, announcement:str=None, confessTalk:bool=False,
    allowMemberInvite:bool=False, autoApprove:bool=False, anonymousChat:bool=False): # 获取修改群设置
        r'mode = get or set'
        payload = {'sessionKey':self.session}
        payload['target'] = target
        if mode == 'get':
            return self.basicsession(Get, 'groupConfig', params=payload)
        elif mode == 'set':
            config = dict(self.groupConfig('get', target))
            config['name'] = name or config['name'] # 群名
            config["announcement"] = announcement or config['announcement'] # 群公告
            config["confessTalk"] = confessTalk or config['confessTalk'] # 坦白说
            config["allowMemberInvite"] = allowMemberInvite or config['allowMemberInvite'] # 群员邀请
            config["autoApprove"] = autoApprove or config['autoApprove'] # 自动审批
            config["anonymousChat"] = anonymousChat # 匿名
            payload['config'] = config
            return self.basicsession(Post, 'groupConfig', data=json.dumps(payload))
        else:
            raise RequestError
    
    def MemberInfo(self, mode, target:int, memberID:int, name:str=None, special:str=None): # 获取修改群员设置
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        if mode == 'get':
            return self.basicsession(Get, 'memverInfo', params=payload)
        elif mode == 'set':
            info = dict(self.memberInfo('get', target, memberID))
            info['name'] = name or info['name'] # 群名称
            info['specialTitle'] = special or info['specialTitle'] # 群头衔
            payload['info'] = info
            return self.basicsession(Post, 'memverInfo', data=json.dumps(payload))

### 文件操作 目前支持群操作 ###

    def _file(self, mode, payload, *args, **kwargs): # 文件接口
        r'mode = list, info, mkdir, delete, move, rename, upload'
        if mode in ['list', 'info']:
            return self.basicsession(Get, f'file/{mode}', data=json.dumps(payload), *args, **kwargs)
        elif mode in ['mkdir', 'delete', 'move', 'rename', 'upload']:
            return self.basicsession(Post, f'file/{mode}', data=json.dumps(payload), *args, **kwargs)
        else:raise RequestError

    def FileList(self, path:str, target:int, DLinfo=False, offset=0, size=100): # 文件列表
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['withDownloadInfo'] = DLinfo
        payload['offset'] = offset
        payload['size'] = size
        return self._file('list', payload)

    def FileInfo(self, path:str, target:int, DLinfo=False): # 文件信息
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['withDownloadInfo'] = DLinfo
        return self._file('info', payload)

    def FileMkdir(self, parh:str, target:int, name): # 创建文件夹
        payload = {'sessionKey':self.session}
        payload['id'] = parh
        payload['target'] = target
        payload['directoryName'] = name
        return self._file('mkdir', payload)

    def FileDelete(self, path:str, target:int): # 删除文件
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        return self._file('delete', payload)

    def FileMove(self, path:str, target:int, movepath:str): # 移动文件
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['moveTo'] = movepath
        return self._file('move', payload)

    def FilereName(self, path:str, target:int, name): # 重命名
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['moveTo'] = name
        return self._file('rename', payload)

    def FileUpload(self, path:str, filepath:str): # 上传群文件
        r'target is the groupID'
        payload = {'sessionKey':self.session}
        payload['type'] = 'group'
        payload['path'] = path
        files = filepath
        return self._file('upload', payload, files=files)

### 多媒体内容上传 ###

    def Upload(self, mode:str, form:str, filepath): # 上传图片或语言
        if mode not in ['Image', 'Voice']:
            raise RequestError
        if form not in ['friend', 'group', 'temp']:
            raise RequestError
        if mode == 'Voice':
            form = 'group'
        payload = {'sessionKey':self.session}
        payload['type'] = form
        files = {'file': open(filepath, 'rb')}
        return self.basicsession(Post, 'upload{mode}', data=json.dumps(payload), files=files)

if __name__ == '__main__':
    from qconf import QConf
    qconf = QConf()
    q = MiraiApi(qconf.qq, qconf.verifyKey)
    print(q.started)