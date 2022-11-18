# -*- coding: utf-8 -*-
import os, requests
from MyQR import myqr

import soup

def imgurltoqr(url,**kwargs):
    tempdir = os.path.join(os.getcwd(),'temp')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    picture = os.path.join(tempdir, os.path.basename(url))
    with open(picture, "wb") as out_file:
        out_file.write(requests.get(url,**kwargs).content)
    version, level, qr_name = myqr.run(
        url,
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
    if Type not in ['Friend','Group']:return
    Group = hasattr(Sender, 'group')
    if Group:target = Sender.group.id
    else:target = Sender.id
    quote = Source.id
    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'Plain':Plain += msg.text
        if msg.type == 'Image':Image.append(msg)
        if msg.type == 'Quote':
            msg = bot.MessageFromId(msg.id)
            if msg != '5':
                Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
            else:
                for n in range(quote-1,quote-11,-1):
                    msg = bot.MessageFromId(n)
                    if type(msg) is not str:
                        Message += [msg for msg in msg.messageChain if msg.type in ['Image','FlashImage']]
    if not Plain.lower().strip().startswith('qr'):return
    words = Plain.strip()[2:]

    tempdir = os.path.join(os.getcwd(),'temp')
    if not os.path.exists(tempdir):
        os.makedirs(tempdir)
    if Image:
        if not words:words = Image[0].url
        picture = os.path.join(tempdir, Image[0].imageId)
        with open(picture, "wb") as out_file:
            out_file.write(requests.get(Image[0].url).content)
    else:picture = None

    if not words:
        bot.SendMessage(Type, target, soup.Plain('没有包含文本，或者关联图片，请尝试直接和图片一起发送'), id=Source.id)
        return
    
    version, level, qr_name = myqr.run(
        words,
        version = 1,
        level = 'H',
        picture = picture,
        colorized = True,
        contrast = 1.0,
        brightness = 1.0,
        save_name = None,
        save_dir = tempdir
    )
    bot.SendMessage(Type, target, soup.Image(path=qr_name), id=Source.id)