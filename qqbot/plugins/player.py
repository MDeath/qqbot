#-*-coding: utf-8-*

import os,json

def onPlug(bot):
    if not hasattr(bot, 'player'):
        try:
            if os.path.exists(bot.conf.Config('player.json')):
                with open(bot.conf.Config('player.json'), 'r', encoding='utf-8') as f:
                    Map = json.load(f)
            else:raise
        except:
            with open(bot.conf.Config('player.json'),'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            Map = []
        setattr(bot, 'player', Map)
        
def onUnplug(bot):
    if hasattr(bot, 'player'):
        with open(bot.conf.Config('player.json'),'w', encoding='utf-8') as f:
                json.dump(bot.player, f, ensure_ascii=False, indent=4)
        delattr(bot, 'player')

def onInterval(bot):
    '''\
    5分钟自动保存'''
    if hasattr(bot, 'player'):
        with open(bot.conf.Config('player.json'),'w', encoding='utf-8') as f:
                json.dump(bot.player, f, ensure_ascii=False, indent=4)