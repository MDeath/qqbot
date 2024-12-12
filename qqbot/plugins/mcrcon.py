import traceback,os
import soup
from admin import admin_ID
from common import DotDict,jsondump,jsonload
from rcon.source import Client
from qqbotcls import QQBotSched

opts = DotDict({
    'host':'',
    'port':,
    'password':''
})

Group = 260715723

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
    return text

def MCRcon(text,p=False):
    try:
        with Client(opts.host, opts.port, passwd=opts.password)as client:
            response = client.run(text)
        if p:print(Formatting2ANSI(response))
        return Formatting2ANSI(response,False)
    except KeyboardInterrupt:exit()
    except:traceback.print_exc()

def onPlug(bot):
    if not os.path.exists(bot.conf.Config('MC')):
        os.mkdir(bot.conf.Config('MC'))
    bot.MC = DotDict()
    if not os.path.exists(bot.conf.Config('MC/players.txt')):
        with open(bot.conf.Config('MC/players.txt'),'w') as f:
            f.write('[]')
    with open(bot.conf.Config('MC/players.txt'),'r') as f:
        bot.MC.players = DotDict(jsonload(f))

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
    players = MCRcon('list')
    if not players:return
    players = players.split(':')[1].split(',')
    count = len(bot.MC.players)
    for player in players:
        if player not in bot.MC.players:
            bot.MC.players.append(player)
            MCRcon(f'give {player} notreepunching:knife/flint')
            MCRcon(f'give {player} notreepunching:axe/flint')
            MCRcon(f'give {player} notreepunching:pickaxe/flint')
    if count != len(bot.MC.players):
        with open(bot.conf.Config('MC/players.txt'),'w') as f:
            jsondump(bot.MC.players,f)

def onQQMessage(bot, Type, Sender, Source, Message):
    Plain = ''

    for msg in Message:
        if msg.type == 'text':Plain += msg.text

    if not (Plain.startswith('/') and Plain != '/'):return
    Plain = Plain[1:].strip()
    if not (Sender.user_id in [f.user_id for f in admin_ID(me=True)] or ('group' == Type and Sender.role=='admin')):return

    r = MCRcon(Plain,True)
    if not r:return
    bot.SendMsg(Type, Source.target, soup.Text(r), reply=Source.message_id)
