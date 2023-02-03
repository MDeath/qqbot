# -*- coding: utf-8 -*-
import os, requests, time
from MyQR import myqr

import soup

def basename(s:str):
    if s.startswith('http://gchat.qpic.cn/'):
        s = s.split('/')[-2]
    else:s = os.path.basename(s)
    for c in ['\\','/',':','*','?','"','<','>','|']:
        s = s.replace(c,'_')
    return s

def imgurl2qr(
        word:str=None,
        picture:str=None,
        **kwargs
    ) -> soup.Image:
    '''
    picture:可以是图片位置,或是图片url
    word:文本内容,为空时可以采用picture
    '''
    if not (word or picture):raise Exception('wrod or picture 不可同时为空')
    
    tempdir = os.path.join(os.getcwd(),f'temp/qr/{time.strftime("%Y-%m-%d",time.localtime())}')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)

    if not word and picture:word = picture

    if picture and picture.startswith('http'):
        resp = requests.get(picture,**kwargs).content

        picture = os.path.join(tempdir, basename(picture))

        if picture[-4:] not in ('.jpg','.png','.bmp','.gif'):
            if resp[6:10] in (b'JFIF', b'Exif'):picture+='.jpg'
            elif resp.startswith(b'\211PNG\r\n\032\n'):picture+='.png'
            elif resp[:6] in (b'GIF87a', b'GIF89a'):picture+='.gif'
            elif resp.startswith(b'BM'):picture+='.bmp'
            else:picture+='.png'

        with open(picture, "wb") as out_file:out_file.write(resp)

    version, level, qr_name = myqr.run(
        word,
        version = 1,
        level = 'H',
        picture = picture,
        colorized = True,
        contrast = 1.0,
        brightness = 1.0,
        save_name = None,
        save_dir = tempdir
    )
    return soup.Image(path=qr_name)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 'qr' 加上 文本
    生成普通QR码
    回复图片发送 'qr'
    生成该图临时QR码
    发送 'qr' 加上 文本 并附带回复 图片
    生成艺术QR码'''
    if Type not in ['Friend', 'Group', 'Temp']:
        return

    if Type == 'Friend':
        target = Sender.id
    elif Type == 'Group':
        target = Sender.group.id
    elif Type == 'Temp':
        target = Sender.id, Sender.group.id

    quote = Source.id
    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
        if msg.type == 'Image':Image.append(msg)
        if msg.type == 'Quote':
            code, msg = bot.MessageId(target,msg.id)
            if not code:
                Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
            else:
                for n in range(quote-1,quote-11,-1):
                    code, msg = bot.MessageId(target,n)
                    if not code:
                        Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
    if not Plain.lower().strip().startswith('qr'):return
    words = Plain.strip()[2:]

    if Image:
        imgurl = Image[0].url
        if not words:words = imgurl
    else:imgurl = None

    if not words:
        bot.SendMessage(Type, target, soup.Plain('没有包含文本，或者关联图片，请尝试直接和图片一起发送'), id=Source.id)
        return
    bot.SendMessage(Type, target, imgurl2qr(words, imgurl), id=Source.id)