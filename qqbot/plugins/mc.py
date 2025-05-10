import os,re,time

from rcon.source import Client

SERVER_NAME = '.'.join(os.path.basename(__file__).split('.')[0:-1]) # 修改插件文件名对应多个服务器

CONFIG = {
    "host":"",
    "port":25575,
    "password":"",
    "target":[
        ['friend', 1064393873],
        # ['group', 931021429], 
    ]
}

DELAY = ['true']*1 + ['false']*9 # 延长游戏时间设置

def Formatting2ANSI(text:str, ansi=True):
    text = text.replace('§0','\033[0;30m' if ansi else '')
    text = text.replace('§1','\033[0;34m' if ansi else '')
    text = text.replace('§2','\033[0;32m' if ansi else '')
    text = text.replace('§3','\033[0;36m' if ansi else '')
    text = text.replace('§4','\033[0;31m' if ansi else '')
    text = text.replace('§5','\033[0;35m' if ansi else '')
    text = text.replace('§6','\033[0;33m' if ansi else '')
    text = text.replace('§7','\033[0;37m' if ansi else '')
    text = text.replace('§8','\033[0;90m' if ansi else '')
    text = text.replace('§9','\033[0;94m' if ansi else '')
    text = text.replace('§a','\033[0;92m' if ansi else '')
    text = text.replace('§b','\033[0;96m' if ansi else '')
    text = text.replace('§c','\033[0;91m' if ansi else '')
    text = text.replace('§d','\033[0;95m' if ansi else '')
    text = text.replace('§e','\033[0;93m' if ansi else '')
    text = text.replace('§f','\033[0;97m' if ansi else '')
    text = text.replace('§k','\033[8m' if ansi else '')
    text = text.replace('§l','\033[1m' if ansi else '')
    text = text.replace('§m','\033[9m' if ansi else '')
    text = text.replace('§n','\033[4m' if ansi else '')
    text = text.replace('§o','\033[3m' if ansi else '')
    text = text.replace('§r','\033[0m' if ansi else '')
    return text+'\n'

class RCONClient(Client):
    def __init__(
        self,
        host: str,
        port: int,
        passwd: str | None = None, 
        timeout: float | None = None,
        frag_threshold: int = 8192
    ):
        self.status = False
        super().__init__(
            host, 
            port, 
            timeout=timeout, 
            passwd=passwd, 
            frag_threshold=frag_threshold
        )
        try:self.connect(True if passwd else False)
        except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError):pass
        else:self.status = True

    def Rcon(self,text,p=False):
        while True:
            try:
                response = self.run(text)
                if response is None:
                    self.close()
                    self.__init__()
                    continue
                if p:print(Formatting2ANSI(response))
                return Formatting2ANSI(response,False)
            except KeyboardInterrupt:
                exit()
            except (ConnectionResetError, ConnectionRefusedError, ConnectionAbortedError, OSError):
                self.__init__(self.host, self.port, passwd=self.passwd)
                if not self.status:return False

if __name__ != '__main__':
    import soup
    from admin import admin_ID
    from common import DotDict,jsondump,jsonload
    from qqbotcls import QQBotSched

    def onPlug(bot):
        opts = DotDict(CONFIG)
        if not os.path.exists(bot.conf.Config(SERVER_NAME)):
            os.mkdir(bot.conf.Config(SERVER_NAME))
        if not os.path.exists(bot.conf.Config(f'{SERVER_NAME}/config.json')):
            with open(bot.conf.Config(f'{SERVER_NAME}/config.json'),'w') as f:
                jsondump(CONFIG, f)
        with open(bot.conf.Config(f'{SERVER_NAME}/config.json'),'r') as f:
            for k,v in jsonload(f).items():
                if isinstance(v, str) and v:opts[k] = v
        MC = DotDict()
        setattr(bot,SERVER_NAME,MC)

        rcon = RCONClient(opts.host, opts.port, passwd=opts.password)
            
        MC.rcon = rcon
        MC.Rcon = rcon.Rcon
        if MC.rcon.status:
            MC.online = rcon.Rcon('list').replace(' ','').strip().split(':')[1]
            MC.online = set(MC.online.split(',')) if MC.online else set()
        if not os.path.exists(bot.conf.Config(f'{SERVER_NAME}/players.txt')):
            with open(bot.conf.Config(f'{SERVER_NAME}/players.txt'),'w') as f:pass
        with open(bot.conf.Config(f'{SERVER_NAME}/players.txt'),'r') as f:MC.players = set(f.read().split())

    def onUnplug(bot):
        getattr(bot, SERVER_NAME).rcon.close()
        delattr(bot, SERVER_NAME)

    @QQBotSched(year=None, 
                month=None, 
                day=None, 
                week=None, 
                day_of_week=None, 
                hour=None, 
                minute=None,
                second=','.join(map(str,range(0,60,1))),
                start_date=None, 
                end_date=None, 
                timezone=None)
    def second(bot):
        MC = getattr(bot,SERVER_NAME)
        old_status = MC.rcon.status
        online = MC.Rcon('list')
        if not old_status and MC.rcon.status:
            for TYPE, ID in CONFIG['target']:
                bot.SendMsg(TYPE, ID, soup.Text(f'{SERVER_NAME} 服务器上线'))
        if old_status and not MC.rcon.status:
            for TYPE, ID in CONFIG['target']:
                bot.SendMsg(TYPE, ID, soup.Text(f'{SERVER_NAME} 服务器离线'))
        if not MC.rcon.status:return
        online = online.replace(' ','').strip().split(':')[1]
        online = set(online.split(',')) if online else set()
        new_players = online - MC.players
        MC.players.update(online)
        login, logout = [], []
        login = online - MC.online
        logout = MC.online - online
        MC.online = online

        # if players:
        #     gimetime = int(MC.Rcon('time query gametime').split(' ')[-1])
        #     MC.Rcon(f'time set {gimetime*0.5}')

        # for player in new_players: # 新玩家
        #     MC.Rcon(f'give {player} notreepunching:knife/flint')
        #     MC.Rcon(f'give {player} notreepunching:axe/flint')
        #     MC.Rcon(f'give {player} notreepunching:pickaxe/flint')

        if new_players:
            with open(bot.conf.Config(f'{SERVER_NAME}/players.txt'),'w') as f:f.write('\n'.join(MC.players))

        if login:
            for TYPE, ID in CONFIG['target']:
                bot.SendMsg(TYPE, ID, soup.Text(f'{", ".join(login)} 加入了游戏'))
        if logout:
            for TYPE, ID in CONFIG['target']:
                bot.SendMsg(TYPE, ID, soup.Text(f'{", ".join(logout)} 退出了游戏'))

        if online: # 有在线玩家延长时间
            if DELAY[0] != DELAY[-1]:
                MC.Rcon(f'gamerule doDaylightCycle {DELAY[0]}')
            DELAY.append(DELAY.pop(0))
        else:MC.Rcon('gamerule doDaylightCycle false') # 没有在线玩家暂停时间

    def onQQMessage(bot, Type, Sender, Source, Message):
        MC = getattr(bot,SERVER_NAME)
        Plain = ''

        for msg in Message:
            if msg.type == 'text':Plain += msg.text

        if Plain != '/' and Plain.startswith('/') and (Sender.user_id in [f.user_id for f in admin_ID(me=True)] or ('group' == Type and Sender.role=='admin')):
            Plain = Plain[1:].strip()

            r = MC.Rcon(Plain,True)
            if not r:return
            bot.SendMsg(Type, Source.target, soup.Text(r), reply=Source.message_id)
        
        elif Plain == 'list':
            bot.SendMsg(Type, Source.target, soup.Text(MC.Rcon('list',True)), reply=Source.message_id)

        elif Plain == 'time':
            GT = int(re.findall(r'\d+',MC.Rcon('time query gametime'))[0]) + 30000
            GD, GH = divmod(GT, 24000)
            GH, GM = divmod(GH, 1000)
            GM = GM * 60 // 1000
            DT = int(re.findall(r'\d+',MC.Rcon('time query daytime'))[0]) + 6000
            D = int(re.findall(r'\d+',MC.Rcon('time query day'))[0]) + 1
            H, M = divmod(DT, 1000)
            M = M * 60 // 1000
            strf = lambda H, M:time.strftime('%H:%M',(1,0,0,H,M,0,0,0,0))
            text = f'''\
    {D} day {strf(H, M)}
    gametime: {GT}
    daytime: {DT}
    day: {D}'''
            bot.SendMsg(Type, Source.target, soup.Text(text), reply=Source.message_id)

if __name__ == '__main__':
    host = input('HOST: ')
    port = int(input('PORT: '))
    passwd = input('PASSWD: ')
    client = RCONClient(host, port, passwd)
    while True:
        try:
            command = input('>')
            if command.lower() in ['q', 'quit', 'exit']:break
            print(client.Rcon(command))
        except KeyboardInterrupt:break