#-*-coding: utf-8-*

import random,os,json
import re
from time import sleep
import traceback

from common import StartDaemonThread
from soup import AtAll,At,Plain

def onPlug(bot):
    if not hasattr(bot, 'player'):
        bot.Plug('player')
    if not hasattr(bot, 'player'):
        bot.Unplug(__file__)
        return

def Reply(bot,Type,target):
    def func(message):
        return bot.SendMessage(Type,target,message)
    return func

class Poke:
    '''
    Poke类用来初始化一个牌堆
    '''
    def __init__(self):
        self.cards = [[face, suite] for face in "♠♥♦♣" for suite in ['A',2,3,4,5,6,7,8,9,10,'J','Q','K']]
        random.shuffle(self.cards)

class Dealer:
    '''
    Dealer类初始化一个荷官
    主要用来实现取牌和发牌的作用
    '''
    def __init__(self):
        self.cards = Poke().cards

    def give_one_card(self):
        '''
        给玩家发牌
        return: list
        '''
        if not self.cards:
            # 重新取一副牌并洗牌
            self.cards.extend(Poke().cards)
        return self.cards.pop()

class Player(object):
    def __init__(self,id,name,bet):
        self.id = id
        self.name = name
        self.bet = bet
        self.over = False
        self.insurance = None
        self.gameover = False
        self.points = [0,0]
        self.cards_in_hand = [[],[]]

    def Over(self):
        if not self.gameover:
            if self.over:self.over=False
            else:self.over=False

    def hand(self,n):
        cards = ''
        for face, suite in self.cards_in_hand[n]:
            cards += face+suite+' '
        return cards

    def now_count(self):
        '''
        更新计数器
        '''
        for i in range(1):
            point = 0
            for face, suite in self.cards_in_hand[i]:
                if suite in ['J', 'Q', 'K']:
                    suite = 10
                if suite == 'A':
                    suite = 1
                point += suite
            # 判断是否有A，如果有A再判断是否大于11，如果是的话A当做1，否的话当做11
            for card in self.cards_in_hand[i]:
                if card[1] == 'A' and point + 10 < 21:
                    self.points[i] = point + 10
                else:
                    self.points[i] = point

    def get(self, hand, *cards):
        '''
        玩家取荷官发的牌，并更新计数器
        param： *cards 一个或多个list类型表示的牌
        '''
        for card in cards:
            self.cards_in_hand[hand].append(card)
        self.now_count() # 重置分数

class TwentyOne(object):
    def __init__(self) -> None:
        self.dealer = Dealer()
        self.stage = None
        self.player = []

    def join(self,player:Player):
        self.player.append(player)

def bet(reply,twentyone:TwentyOne):
    '下注等待时间'
    twentyone.stage = 'bet' # 玩家加入阶段
    for i in range(90,0,-1):
        if twentyone.stage == 'bet'and i == 30:reply([Plain(f'下注阶段剩余 30 秒')])
        if twentyone.stage == 'bet'and i == 10:reply([Plain(f'下注阶段剩余 10 秒')])
        if twentyone.stage == 'bet'and i == 5:reply([Plain(f'下注阶段剩余 5 秒')])
        sleep(1)
    if twentyone.stage == 'bet':
        twentyone.stage = 'start'

def insurance(reply,twentyone:TwentyOne):
    twentyone.stage = 'insurance' # 下保险阶段
    for i in range(90,0,-1):
        if twentyone.stage == 'insurance'and i == 30:reply([Plain(f'下注阶段剩余 30 秒')])
        if twentyone.stage == 'insurance'and i == 10:reply([Plain(f'下注阶段剩余 10 秒')])
        if twentyone.stage == 'insurance'and i == 5:reply([Plain(f'下注阶段剩余 5 秒')])
        sleep(1)
    if twentyone.stage == 'insurance':
        twentyone.stage = 'start'

    def free(self):pass

    def end(slef):pass

    def close(self):pass

def main(bot,reply,twentyone:TwentyOne):
    try:
        StartDaemonThread(bet,reply,twentyone) # 倒计时开始
        while twentyone.stage != 'start':pass # 人数满足或倒计时结束跳出阻塞
        
        if not len(twentyone.player):
            reply([Plain('没人玩退了')])
            return # 没有人玩退出

        reply([Plain('开始发牌')])
        robot = Player(bot.conf.qq,'庄家',0)# 添加庄家
        dealer = twentyone.dealer # 荷官
        for player in twentyone.player: # 每人发两张牌
            player.get(0, dealer.give_one_card(), dealer.give_one_card())
            if player.points[0] == 21:
                reply([Plain("玩家"),At(player.id),Plain(f"手中的牌是 {player.hand()} 黑杰克！")])
                player.gameover = True
            else:
                reply([Plain("玩家"),At(player.id),Plain(f"手中的牌是 {player.hand()}")])

        reply([Plain(f"电脑手中的牌是 ?? {robot.cards_in_hand[0][1][0]+robot.cards_in_hand[0][1][1]}")])
        if robot.cards_in_hand[0][1][1] == 'A':
            reply([Plain('电脑的第二张牌是A，是否要加一半押金作为保险？如果电脑为黑杰克直接获得两倍奖励')])
            StartDaemonThread(insurance,reply,twentyone)
            while twentyone.stage != 'start':pass # 全员选择完毕或倒计时结束跳出阻塞
            if robot.points == 21:
                reply([Plain('电脑是黑杰克！')])
    except:
        reply([Plain(traceback.format_exc())])

def onQQMessage(bot, Type, Sender, Source, Message):
    if not hasattr(bot,'player'):return
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = Sender.id, Sender.group.id

    message = []
    if hasattr(Sender, 'group'):
        target = Sender.group.id
        message.append(At(Sender.id))
    else:
        target = Sender.id
        Sender.memberName = Sender.nickname
    
    reply = Reply(bot,Type,target)

    for p in bot.player:
        if p == id:break
    else:
        p = {'id':Sender.id,'chip':100}
        bot.player.append(p)

    commad = ''
    for msg in Message:
        if msg.type == 'Plain':commad += msg.text
    try:
        for t in getattr(bot,Type):
            if t.id == target:break
        twentyone = getattr(t,'twentyone',None)
        if twentyone is None and commad in ['21点', '玩21点']: # 如果对象不在游戏中开始游戏
            reply([Plain('21点已开桌，开始下注吧')])
            twentyone = TwentyOne()
            StartDaemonThread(main,bot,reply,twentyone)
        if twentyone is None:return # 以下为指令

        dealer = twentyone.dealer
        if '下注'in commad:
            if twentyone.stage == 'bet' and len(twentyone.player)<6: # 如果对象在下注阶段且下注的玩家小于6人,可以下注
                for t in twentyone.player:
                    if t.id == Sender.id:
                        message.append(Plain(f'下注失败，你以下注 {t.bet}'))
                        reply(message)
                        return
                try:bet = int(commad.replace('下注',''))
                except:
                    message.append(Plain('下注失败，除了关键字 下注 以外，其余为赌注'))
                    reply(message)
                    return
                if bet > p['chip']:
                    message.append(Plain(f"下注失败，余额仅剩 {p['chip']}"))
                    reply(message)
                    return
                if bet < 10:
                    message.append(Plain(f"下注失败，赌注不能小于10"))
                    reply(message)
                    return
                p['chip'] -= bet
                player = Player(Sender.id,Sender.memberName,bet)
                twentyone.join(player)
                message.append(Plain(f"成功下注 {bet},余额仅剩 {p['chip']}"))
                reply(message)
                reply([Plain(f"现有玩家 {[t.name for t in twentyone.player]}")])
                if len(twentyone.player) == 7 or twentyone.type == "Friend":
                    twentyone.stage = 'start'
                return
            else:
                message.append(Plain(f"下注阶段已结束,请等待下回合"))
                reply(message)
                return
        
        if twentyone.stage == 'insurance' and commad == '下保险':
            for player in twentyone.player:
                if player.id == Sender.id:break
            if player.insurance is True:
                message.append(Plain('你已经买过保险'))
                reply(message)
            elif player.insurance is None and player.bet // 2 > p['chip']:
                message.append(Plain(f"余额仅剩 {p['chip']}，无法下保险"))
                reply(message)
                player.insurance = False
            elif player.insurance is None and player.bet // 2 <= p['chip']:
                message.append(Plain(f"买保险成功，余额仅剩 {p['chip']}"))
    except:
        reply([Plain(traceback.format_exc())])

if __name__ == '__main__':
    computer = Player('Robot')
    human = Player('Lihaoer')
    dealer = Dealer()
    main(dealer, computer, human)