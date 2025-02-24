import traceback,os,time

from rcon.source import Client

config = {
    "host":"",
    "port":25575,
    "password":""
}

target = [
    ['friend', 1064393873],
    ['group', 931021429], 
]

worklist = []

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

class RCON(Client):
    def __init__(
        self,
        host: str,
        port: int,
        passwd: str | None = None, 
        timeout: float | None = None,
        frag_threshold: int = 8192):
        super().__init__(
            host, 
            port, 
            timeout=timeout, 
            passwd=passwd, 
            frag_threshold=frag_threshold
        )

    def Rcon(self,text,p=False):
        while True:
            try:
                response = self.run(text)
                if p:print(Formatting2ANSI(response))
                return Formatting2ANSI(response,False)
            except KeyboardInterrupt:
                exit()
            except ConnectionResetError:
                self.__init__(self.host, self.port, passwd=self.passwd)
                self.connect(True)
            except ConnectionRefusedError:
                self.__init__(self.host, self.port, passwd=self.passwd)
                self.connect(True)
            except ConnectionAbortedError:
                self.__init__(self.host, self.port, passwd=self.passwd)
                self.connect(True)

if __name__ != '__main__':
    import soup
    from admin import admin_ID
    from common import DotDict,jsondump,jsonload
    from qqbotcls import QQBotSched

    def onPlug(bot):
        opts = DotDict(config)
        if not os.path.exists(bot.conf.Config('MC')):
            os.mkdir(bot.conf.Config('MC'))
        if not os.path.exists(bot.conf.Config('MC/config.json')):
            with open(bot.conf.Config('MC/config.json'),'w') as f:
                jsondump(config, f)
        with open(bot.conf.Config('MC/config.json'),'r') as f:
            for k,v in jsonload(f).items():
                if isinstance(v, str) and v:opts[k] = v
        bot.MC = DotDict()

        rcon = RCON(opts.host, opts.port, passwd=opts.password)
        rcon.connect(True)
        bot.MC.rcon = rcon
        bot.MC.Rcon = rcon.Rcon
        bot.MC.online = rcon.Rcon('list').strip().split(':')[1]
        bot.MC.online = set(bot.MC.online.split(', ')) if bot.MC.online else set()
        if not os.path.exists(bot.conf.Config('MC/players.txt')):
            with open(bot.conf.Config('MC/players.txt'),'w') as f:pass
        with open(bot.conf.Config('MC/players.txt'),'r') as f:bot.MC.players = set(f.read().split())

    def onUnplug(bot):
        bot.MC.rcon.close()
        delattr(bot, 'MC')

    @QQBotSched(year=None, 
                month=None, 
                day=None, 
                week=None, 
                day_of_week=None, 
                hour=None, 
                minute=None, 
                second='0,5,10,15,20,25,30,35,40,45,50,55', 
                start_date=None, 
                end_date=None, 
                timezone=None)
    def NewPlayer(bot):
        players = bot.MC.Rcon('list').strip().split(':')[1]
        players = set(players.split(', ')) if players else set()
        new = players - bot.MC.players
        bot.MC.players.update(players)
        login = players - bot.MC.online
        logout = bot.MC.online - players
        bot.MC.online = players

        for player in new:
            bot.MC.Rcon(f'give {player} notreepunching:knife/flint')
            bot.MC.Rcon(f'give {player} notreepunching:axe/flint')
            bot.MC.Rcon(f'give {player} notreepunching:pickaxe/flint')
        if login:
            for TYPE, ID in target:
                bot.SendMsg(TYPE, ID, soup.Text(f'{", ".join(login)} 加入了游戏'))
        if logout:
            for TYPE, ID in target:
                bot.SendMsg(TYPE, ID, soup.Text(f'{", ".join(logout)} 退出了游戏'))
        if new:
            with open(bot.conf.Config('MC/players.txt'),'w') as f:f.write('\n'.join(bot.MC.players))

    def onQQMessage(bot, Type, Sender, Source, Message):
        Plain = ''

        for msg in Message:
            if msg.type == 'text':Plain += msg.text

        if Plain != '/' and Plain.startswith('/') and (Sender.user_id in [f.user_id for f in admin_ID(me=True)] or ('group' == Type and Sender.role=='admin')):
            Plain = Plain[1:].strip()

            r = bot.MC.Rcon(Plain,True)
            if not r:return
            bot.SendMsg(Type, Source.target, soup.Text(r), reply=Source.message_id)
        
        elif Plain == 'list':
            bot.SendMsg(Type, Source.target, soup.Text(bot.MC.Rcon('list',True)), reply=Source.message_id)

        elif Plain == 'time':
            GT = int(bot.MC.Rcon('time query gametime')[8:]) + 30000
            GD, GH = divmod(GT, 24000)
            GH, GM = divmod(GH, 1000)
            GM = GM * 60 // 1000
            DT = int(bot.MC.Rcon('time query daytime')[8:]) + 6000
            D = int(bot.MC.Rcon('time query day')[8:]) + 1
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
    client = RCON(host, port, passwd)
    client.connect(True if passwd else False)
    while True:
        try:
            command = input('>')
            if command.lower() in ['q', 'quit', 'exit']:break
            print(client.Rcon(command))
        except KeyboardInterrupt:break