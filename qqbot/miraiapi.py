# -*- coding: utf-8 -*-

from common import DotDict
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
import json, os, requests, time, traceback

class RequestError(Exception):
    pass

class MiraiApi():
    def __init__(self, qq, verifyKey, host='localhost', port=8080, session=None, timeout=3) -> None:
        self.started = False
        self.host = host
        self.port = port
        self.timeout = timeout
        self.qq = int(qq)
        self.verifyKey = verifyKey
        self.session = session
        if not self.session:self.verify()
    
    ErrorCode = None
    ErrorTime = None

    def ErrorAnalyst(self, r) -> None:
        if self.ErrorCode != r.code or time.time()-self.ErrorTime > 60:
            ERROR(f'Code:{r.code}, Msg:{r.msg}')
        self.ErrorCode, self.ErrorTime = r.code, time.time()
        if r.code == 1: # 错误的verify key
            self.verifyKey = input('VerifyKey:')
        elif r.code == 2:pass # 指定的Bot不存在
        elif r.code == 3: # Session失效或不存在
            self.verify()
        elif r.code == 4: # Session未认证(未激活)
            self.started = False
            self.bind()
        elif r.code == 5:pass # 发送消息目标不存在(指定对象不存在)
        elif r.code == 6:pass # 指定文件不存在，出现于发送本地图片
        elif r.code == 10:pass # 无操作权限，指Bot没有对应操作的限权
        elif r.code == 20:pass # Bot被禁言，指Bot当前无法向指定群发送消息
        elif r.code == 30:pass # 消息过长
        elif r.code == 400:pass # 错误的访问，如参数错误等
        elif r.code == 500:pass # MCL内部错误，或其他原因

    def basicsession(self, mode, url, **kwargs):
        if mode == 'get' and 'timeout' not in kwargs:kwargs['timeout'] = self.timeout
        while not self.started and url not in ('verify','bind','botList'):pass
        while True:
            try:
                r = DotDict(getattr(requests, mode)(f'http://{self.host}:{self.port}/{url}', **kwargs).text)
                break
            except requests.exceptions.ConnectionError:
                ERROR('无法连接倒Mirai，请检查服务、地址、端口。')
            except requests.exceptions.ReadTimeout:
                os.popen('taskkill /f /im java.exe').read()
                ERROR('Mirai失去意识，敲打中。')
            except Exception as e:
                raise RequestError(e)
        if hasattr(r, 'code') and r.code:
            self.ErrorAnalyst(r)
            return r.code, f'Code:{r.code}, Msg:{r.msg}'
        if hasattr(r, 'data'):
            return r.code, r.data
        elif hasattr(r, 'messageId'):
            return r.code, r.messageId
        elif hasattr(r, 'msg'):
            return r.code, r.msg
        else:
            return r

    def verify(self) -> None:
        '''认证
    verifyKey   创建Mirai-Http-Server时生成的key，可在启动时指定或随机生成
        '''
        self.started = False
        payload = {"verifyKey": self.verifyKey}
        while not self.started:
            r = self.basicsession('post', 'verify', json=payload)
            if hasattr(r,'session'):
                self.session = r.session
                INFO('认证成功')
                self.bind()
                return
            time.sleep(1)

    def bind(self, qq=None) -> None:
        '''绑定
    qq      Session将要绑定的Bot的qq号
    session 你的session key
        '''
        flag = True
        while self.qq not in self.BotList()[1]:
            time.sleep(5)
            if self.qq in self.BotList()[1]:break
            os.popen('taskkill /f /im java.exe').read()
            if flag:
                flag = WARNING(f'qq:{self.qq} 未登录')
        payload = {
            "sessionKey": self.session,
            "qq": qq or self.qq
        }
        code, r = self.basicsession('post', 'bind', json=payload)
        if code == 0:
            INFO('绑定成功')
            self.started = True
            return
        time.sleep(1)

    def BotList(self) -> list:
        '获取登录账号'
        return self.basicsession('get', 'botList')

    def SessionInfo(self) -> DotDict:
        '获取会话信息'
        return self.basicsession('get', f'sessionInfo?sessionKey={self.session}')

### 消息与事件 ###
    def pollForever(self, MessageAnalyst): # http
        while True:
            try:
                code, result = self.Mirai.GetMessage()
            except:
                ERROR('qsession.Poll 方法出错', exc_info=True)
            else:
                if not result:continue
                for r in result:
                    MessageAnalyst(r)
                    
    def pollForever(self, MessageAnalyst): # websocket
        import websocket
        while True:
            try:
                self.ws = websocket.create_connection(f'ws://{self.host}:{self.port}/all?verifyKey={self.verifyKey}&sessionKey={self.session}')
            except:
                self.verify()
                time.sleep(1)
                continue
            recv = self.ws.recv()
            while self.started:
                try:
                    MessageAnalyst(DotDict(self.ws.recv()).data)
                except Exception as e:
                    WARNING(e)
                    break

    def countMessage(self) -> int:
        '查看队列大小'
        return self.basicsession('get', f'countMessage?sessionKey={self.session}')

    def GetMessage(
        self, 
        count:int=1,
        last=True,
        pop=True
    ) -> tuple([int, list]):
        '''获取或查看消息与事件
    count   获取(查看)消息和事件的数量
    last    时间倒序，否则正序
    pop     获取后移除
        '''
        payload = {'sessionKey':self.session}
        payload['count'] = count
        return self.basicsession('get', f'{"fetch" if pop else "peek"}{"Latest" if last else ""}Message', params=payload)

    def MessageId(
        self, 
        target:int,
        id:int
    ) -> tuple([int, DotDict]):
        '''通过MessageID获取消息
    target      好友id或群id
    messageID   获取消息的messageId
        '''
        payload = {'sessionKey':self.session,'messageId':id, 'target':target}
        return self.basicsession('get', 'messageFromId', params=payload)

    def SendMessage(
        self, 
        type:str, # 发送对象类型
        target:int|tuple|list, # 对象ID
        *message:dict, # 消息链
        id:int=None # 回复ID
    ) -> tuple([int, int]):
        r'''发给好友、群、临时消息
    type    friend, group, temp
    target  发送消息目标
        group:  target = groupID
        friend: target = qqID
        temp:   target = groupID, qqID
    message 消息链，是一个消息对象构成的数组
    id      引用一条消息的messageId进行回复
        '''
        type = type.title()
        if type not in ['Friend', 'Group', 'Temp']:raise RequestError
        payload = {'sessionKey':self.session}
        if type != 'temp':payload['target'] = target
        else:payload['group'], payload['qq'] = target
        payload['messageChain'] = message
        if id:payload['quote'] = id
        code, msgid = self.basicsession('post', f'send{type}Message', json=payload)
        INFO(f'发到 {type} {target}({msgid or code}){(id and "回复消息("+str(id)+")") or ""}:\n{message}')
        return code, msgid

    def Nudge(
        self, 
        type:str, 
        target:int, 
        id:int
    ) -> tuple([int, str]):
        r'''戳一戳
    kind    上下文类型, 可选值 friend, group, stranger
    target  戳一戳接受主体(上下文), 戳一戳信息会发送至该主体, 为群号/好友QQ号
    id      戳一戳的目标, QQ号, 可以为 bot QQ号
        '''
        type = type.title()
        if type not in ['Friend', 'Group', 'Stranger']:raise RequestError
        payload = {'sessionKey':self.session}
        payload['subject'] = target
        payload['target'] = id
        payload['kind'] = type
        self.basicsession('post', 'sendNudge', json=payload)

    def Recall(
        self, 
        target:int, 
        id:int
    ) -> tuple([int, str]):
        '''撤回消息
        target  好友id或群id
        id      需要撤回的messageId
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['messageId'] = id
        return self.basicsession('post', '/recall', json=payload)

    def Roaming(
        self, 
        target:int, 
        start:int|str=0, 
        end:int|str=0
    ) -> tuple([int, list]):
        '''获取漫游消息
    target  漫游消息对象，好友id，目前仅支持好友漫游消息
    start   起始时间, UTC+8 时间戳, 单位为秒. 可以为 0, 即表示从可以获取的最早的消息起. 负数将会被看是 0.
    end     结束时间, UTC+8 时间戳, 单位为秒. 可以为 Long.MAX_VALUE, 即表示到可以获取的最晚的消息为止. 低于 timeStart 的值将会被看作是 timeStart 的值.
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['start'] = start
        payload['end'] = end
        return self.basicsession('post', 'roamingMessages', json=payload)
        
    def event_response(
        self, 
        even, 
        operate:int=0,
        msg:str='' 
    ) -> None:
        '''事件处理
    even    事件对象
    operate 响应的操作类型
        好友申请 0(同意)|1(拒绝)|2(拉黑)
        进群申请 0(同意)|1(拒绝)|2(忽略)|3(拒绝拉黑)|4(忽略拉黑)
        拉群申请 0(同意)|1(拒绝)
    msg     回复的信息
        '''
        payload = {'sessionKey':self.session}
        payload['eventId'] = even.eventId
        payload['fromId'] = even.fromId
        payload['groupId'] = even.groupId
        payload['operate'] = operate
        payload['message'] = msg
        type = even.type[0].lower() + even.type[1:]
        self.basicsession('post', f'resp/{type}', json=payload)

### 联系人操作 ###
    def List(
        self, 
        type:str, 
        id:int=None
    ) -> list:
        '''获取好友、群、成员列表
    type    friend 好友列表、group 群列表、member 成员列表
    id      指定群的群号
        '''
        type = type.lower()
        if type not in ['friend', 'group', 'member']:raise RequestError
        payload = {'sessionKey':self.session}
        if type == 'member':payload['target'] = id
        return self.basicsession('get', f'{type}List', params=payload)

    def Profile(
        self, 
        type:str, 
        target:int=None, 
        memberID:int=None
    ) -> DotDict:
        r'''获取bot、好友、成员资料
    type    bot Bot资料、friend 好友资料、member 群成员资料
    target  好友账号或群号
    member  群成员QQ号码
        '''
        type = type.lower()
        if type not in ['bot', 'friend', 'member']:raise RequestError
        payload = {'sessionKey':self.session}
        if type != 'bot':
            payload['target'] = target
        if type == 'member':
            payload['memberId'] = memberID
        return self.basicsession('get', f'{type}Profile', params=payload)

    def DelFriend(self, target:int) -> tuple([int, str]):
        r'''删除好友
    target  好友账号
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        return self.basicsession('post', 'deleteFriend', json=payload)

### 群管理 ###
    def Mute(
        self, 
        target:int, 
        memberID:int, 
        time:int=0
    ) -> tuple([int, str]):
        r'''禁言
    target  群号
    member  群成员QQ号码
    time    时长（秒）
        '''
        print(bool(time),time)
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        if time:payload['time'] = time
        return self.basicsession('post', f'{"" if time else "un"}mute', json=payload)
 # 移除成员
    def Kick(
        self, 
        target:int, 
        memberID:int, 
        msg:str='您已被移出群聊'
    ) -> tuple([int, str]):
        r'''移除成员
    target  群号
    member  群成员QQ号码
    msg     通知消息
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        payload['msg'] = msg
        return self.basicsession('post', 'kick', json=payload)
 # 退群
    def Quit(self, target:int) -> tuple([int, str]):
        r'''退群
    target  群号
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        return self.basicsession('post', 'quit', json=payload)
 # 全体禁言
    def MuteAll(
        self, 
        target:int, 
        mute:bool=True
    ) -> tuple([int, str]):
        r'''全体禁言
    target  群号
    mute    真（禁）/假（解）
    '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        return self.basicsession('post', f'{"" if mute else "un"}muteAll', json=payload)
 # 设置群精华消息
    def SetEssence(
        self, 
        target:int, 
        messageID:int
    ):
        r'''设置群精华消息
    target  群号
    id      需要加精消息的messageId
        '''
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['messageId'] = messageID
        return self.basicsession('post', 'setEssence', json=payload)
 # 获取或修改群设置
    def GroupConfig(
        self, 
        mode, 
        target:int, 
        name:str=None, 
        announcement:str=None, 
        confessTalk:bool=False,
        allowMemberInvite:bool=False, 
        autoApprove:bool=False, 
        anonymousChat:bool=False
    ) -> DotDict or tuple([int,str]):
        r'''获取或修改群设置
        '''
        r'mode = get or set'
        payload = {'sessionKey':self.session}
        payload['target'] = target
        if mode == 'get':
            return self.basicsession('get', 'groupConfig', params=payload)
        elif mode == 'set':
            payload['config'] = {}
            if name:payload['config']['name'] = name                                           # 群名
            if announcement:payload['config']["announcement"] = announcement                   # 群公告
            if confessTalk:payload['config']["confessTalk"] = confessTalk                      # 坦白说
            if allowMemberInvite:payload['config']["allowMemberInvite"] = allowMemberInvite    # 群员邀请
            if autoApprove:payload['config']["autoApprove"] = autoApprove                      # 自动审批
            if anonymousChat:payload['config']["anonymousChat"] = anonymousChat                # 匿名
            return self.basicsession('post', 'groupConfig', json=payload)
        else:
            raise RequestError
 # 获取修改群员设置
    def MemberInfo(self, mode, target:int, memberID:int, name:str=None, special:str=None) -> DotDict or tuple([int,str]):
        r'mode = get or set'
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        if mode == 'get':
            return self.basicsession('get', 'memberInfo', params=payload)
        elif mode == 'set':
            payload['info'] = {}
            payload['info']['name'] = name              # 群名称
            payload['info']['specialTitle'] = special   # 群头衔
            return self.basicsession('post', 'memberInfo', json=payload)
 # 修改群员管理员
    def MemberAdmin(self, target:int, memberID:int) -> tuple([int, str]):
        payload = {'sessionKey':self.session}
        payload['target'] = target
        payload['memberId'] = memberID
        payload['assign'] = True if self.MemberInfo('get',target,memberID).permission == 'MEMBER' else False
        return self.basicsession('post', 'memberInfo', json=payload)
 # 获取群公告
    def AnnoList(self, target:int, offset:int=None, size:int=None):
        payload = {'id':target}
        if offset:payload['offset'] = offset
        if size:payload['size'] = size
        return self.basicsession('get', 'memberInfo', params=payload)
 # 发布群公告
    def AnnoPut(
        self, 
        target:int, # 群号
        content:str, # 	公告内容
        image:dict|list|tuple=None, # 公告图片url|path|base64
        top=False, # 是否置顶
        popup=False, # 是否自动弹出
        confirm=False, # 是否需要群成员确认
        NewMember=False, # 是否发送给新成员
        EditCard=False # 是否显示群成员修改群名片的引导
    ) -> tuple([int, list]):
        payload = {'id':target}
        if content:payload['content'] = content
        if image:
            if type(image) is image:image = [image.keys()[0].title(),image.values()[0]]
            payload[image[0] if image[0].startswith('image') else f'image{image[0]}'] = image[1]
        if top:payload['pinned'] = top
        if popup:payload['showPopup'] = popup
        if confirm:payload['requireConfirmation'] = confirm
        if NewMember:payload['sendToNewMember'] = NewMember
        if EditCard:payload['showEditCard'] = EditCard
        return self.basicsession('post', 'memberInfo', json=payload)
 # 删除群公告
    def AnnoDel(
        self, 
        target:int, # 群号
        fid:str # 群公告唯一id
    ) -> tuple([int, str]):
        payload = {'id':target}
        payload['fid'] = fid
        return self.basicsession('post', 'memberInfo', json=payload)

### 多媒体内容上传 ###
 # 上传图片或语音
    def Upload(self, f, Type:str='friend', mode:str='image') -> DotDict:
        mode = mode.title()
        Type = Type.lower()
        if mode not in ['Image', 'Voice']:
            raise RequestError
        if Type not in ['friend', 'group', 'temp']:
            raise RequestError
        if mode == 'Voice':
            Type = 'group'
        payload = {'sessionKey':self.session}
        payload['type'] = Type
        files = {'img': open(f, 'rb') if type(f) is str else f}
        return self.basicsession('post', f'upload{mode}', data=payload, files=files)

### 文件操作 目前支持群操作 ###
 # 文件接口
    def _file(self, mode, payload, *args, **kwargs):
        r'mode = list, info, mkdir, delete, move, rename, upload'
        if mode in ['list', 'info']:
            return self.basicsession('get', f'file/{mode}', params=json.dumps(payload), *args, **kwargs)
        elif mode in ['mkdir', 'delete', 'move', 'rename', 'upload']:
            return self.basicsession('post', f'file/{mode}', data=json.dumps(payload), *args, **kwargs)
        else:raise RequestError
 # 文件列表
    def FileList(self, target:int, path:str, DLinfo=False, offset=0, size=100):
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        if DLinfo:payload['withDownloadInfo'] = DLinfo
        payload['offset'] = offset
        payload['size'] = size
        return self._file('list', payload)
 # 文件信息
    def FileInfo(self, target:int, path:str, DLinfo=False):
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['withDownloadInfo'] = DLinfo
        return self._file('info', payload)
 # 创建文件夹
    def FileMkdir(self, target:int, parh:str, name):
        payload = {'sessionKey':self.session}
        payload['id'] = parh
        payload['target'] = target
        payload['directoryName'] = name
        return self._file('mkdir', payload)
 # 删除文件
    def FileDel(self, target:int, path:str):
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        return self._file('delete', payload)
 # 移动文件
    def FileMove(self, target:int, path:str, movepath:str):
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['moveTo'] = movepath
        return self._file('move', payload)
 # 重命名
    def FilereName(self, target:int, path:str, name):
        payload = {'sessionKey':self.session}
        payload['id'] = path
        payload['target'] = target
        payload['moveTo'] = name
        return self._file('rename', payload)
 # 上传群文件
    def FileUpload(self, target:int, path:str, filepath:str):
        r'target is the groupID'
        payload = {'sessionKey':self.session}
        payload['type'] = 'group'
        payload['path'] = path
        payload['target'] = target
        files = {'img': open(filepath, 'rb') if type(filepath) is str else filepath}
        return self._file('upload', payload, files=files)

if __name__ == '__main__':
    import soup
    from qconf import QConf
    qconf = QConf()
    bot = MiraiApi(qconf.qq, qconf.verifyKey)
    print(qconf.qq, bot.started)
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