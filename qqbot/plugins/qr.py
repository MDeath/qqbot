# -*- coding: utf-8 -*-
import cloudscraper, os, time
from amzqr import amzqr

from qqbotcls import bot
from common import JsonDict, b64decode
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
import soup

requests = cloudscraper.create_scraper()

tempdir = os.path.join(os.getcwd(),'temp','qr')
def get_tempdir():
    temppath = os.path.join(tempdir,time.strftime('%Y-%m-%d',time.localtime()))
    if not os.path.exists(temppath):
        os.makedirs(temppath)
    return temppath

# ===中文支持 UTF-8 转 UTF-16 需要去 amzqr 替换以下开头===
'''
def run(words, version=1, level='H', picture=None, colorized=False, contrast=1.0, brightness=1.0, save_name=None, save_dir=os.getcwd()):

    supported_chars = r"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ··,.:;+-*/\~!@#$%^&`'=<>[]()?_{}|"


    # check every parameter
    if not isinstance(words, str) or any(i not in supported_chars for i in words):
        raise ValueError('Wrong words! Make sure the characters are supported!')
'''
# ===中文支持 UTF-8 转 UTF-16 需要去 amzqr 替换以上开头===
# ===中文支持 UTF-8 转 UTF-16 需要去 amzqr 替换成以下开头===
'''
def utf16to8(input_txt: str) -> str:
    out = []
    for idx in range(len(input_txt)):
        ch = ord(input_txt[idx])
        if 0x0001 <= ch <= 0x007f:
            out.append(input_txt[idx])
        elif ch > 0x07ff:
            out.append(chr(0xE0 | (ch >> 12 & 0x0F)))
            out.append(chr(0x80 | (ch >> 6 & 0x3F)))
            out.append(chr(0x80 | (ch >> 0 & 0x3F)))
        else:
            out.append(chr(0xC0 | (ch >> 6) & 0x1f))
            out.append(chr(0x80 | (ch >> 0) & 0x3f))

    return ''.join(out)

def run(words, version=1, level='H', picture=None, colorized=False, contrast=1.0, brightness=1.0, save_name=None, save_dir=os.getcwd()):

    supported_chars = r"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ··,.:;+-*/\~!@#$%^&`'=<>[]()?_{}|"
    words = utf16to8(words)
    
    # check every parameter
    # if not isinstance(words, str) or any(i not in supported_chars for i in words):
    if not isinstance(words, str):
        raise ValueError('Wrong words! Make sure the characters are supported!')
'''
# ===中文支持 UTF-8 转 UTF-16 需要去 amzqr 替换成以上开头===
# ===多线程支持需要去 amzqr 替换以下开头===
'''
    tempdir = os.path.join(os.path.expanduser('~'), '.myqr')
'''
# ===多线程支持需要去 amzqr 替换以上开头===
# ===多线程支持需要去 amzqr 替换成以下开头===
'''
    try:tempdir = os.path.join(os.path.expanduser('~'), '.myqr', os.path.splitext(os.path.basename(picture))[0])
    except:tempdir = os.path.join(os.path.expanduser('~'), '.myqr', '_')
'''
# ===多线程支持需要去 amzqr 替换成以上开头===

def basename(s:str):
    if s.startswith('http://gchat.qpic.cn/') or s.startswith('http://c2cpicdw.qpic.cn/'):
        s = s.split('/')[-2]
    else:s = os.path.basename(s)
    for c in ['\\','/',':','*','?','"','<','>','|']:
        s = s.replace(c,'_')
    return s

def fwimg2qr(nodeList:soup.Node): # messageId=-1，全部图片转QRCode
    for node in nodeList:
        for m in range(len(node.messageChain)):
            if node.messageChain[m].type == 'Image':
                if 'url' in node.messageChain[m]:
                    try:
                        content = requests.get(node.messageChain[m].url).content
                    except:
                        content = None
                elif 'path' in node.messageChain[m]:
                    content = node.messageChain[m].path
                else:
                    continue
                try:
                    if not content:raise
                    url = bot.Upload(content).url
                    node.messageChain[m] = img2qr(picture=url)
                except:
                    node.messageChain[m] = img2qr(node.messageChain[m].url)
    return nodeList

def img2qr(
        word:str=None,
        picture:str|JsonDict=None,
        **kwargs
    ) -> soup.Image:
    '''
    word:文本内容,为空时可以采用picture
    picture:可以是本地路径,或是图片url
    或soup.Image和soup.FlashImage(至少包含url)
    '''
    if not (word or picture):raise Exception('wrod or picture 不可同时为空')
    
    file_name, imgurl = time.strftime("%H-%M-%S",time.localtime()), False
    if isinstance(picture, JsonDict):
        imgurl = picture.url
        if not word and picture:
            word = picture.url

        if 'imageId' in picture:
            file_name = picture.imageId
        elif 'id' in picture:
            file_name = picture.id
        elif picture.url.endswith(('.jpg','.png','.bmp','.gif')):
            file_name = picture.url
    elif isinstance(picture,str) and picture.startswith('http'):
        imgurl = picture
        if not word and picture:
            word = picture

        if picture.endswith(('.jpg','.png','.bmp','.gif')):
            file_name = picture
    
    if imgurl:
        try:
            byte = requests.get(imgurl,**kwargs).content
            if not file_name.endswith(('.jpg','.png','.bmp','.gif')):
                if byte[6:10] in (b'JFIF', b'Exif'):file_name+='.jpg'
                elif byte.startswith(b'\211PNG\r\n\032\n'):file_name+='.png'
                elif byte[:6] in (b'GIF87a', b'GIF89a'):file_name+='.gif'
                elif byte.startswith(b'BM'):file_name+='.bmp'
                else:file_name+='.png'
            picture = os.path.join(get_tempdir(), basename(file_name))
            with open(picture, "wb") as f:f.write(byte)
        except:
            picture = None
        
    version, level, qr_name = amzqr.run(
        word,
        version = 1,
        level = 'L',
        picture = picture,
        colorized = True,
        contrast = 1.0,
        brightness = 1.0,
        save_name = None,
        save_dir = get_tempdir()
    )
    with open(qr_name, 'rb') as f:
        return soup.Image(base64=f.read())

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
    Plain = ''.join([msg.text for msg in Message if msg.type == 'Plain']).strip()
    if not Plain.lower().startswith('qr'):return
    Image = None
    for msg in Message:
        if msg.type == 'Image':
            Image = msg
            break
        if msg.type == 'Quote':
            r = bot.MessageId(target,msg.id)
            if not r.code:
                Message += [msg for msg in r.data.messageChain if msg.type in ['Image','FlashImage']]
            else:
                for n in range(quote-1,quote-11,-1):
                    r = bot.MessageId(target,n)
                    if not r.code:
                        Message += [msg for r.data in r.msg.messageChain if msg.type in ['Image','FlashImage']]
    words = Plain.strip()[2:]

    if not words and not Image:
        bot.SendMessage(Type, target, soup.Plain('没有包含文本，或者关联图片，请尝试直接和图片一起发送'), id=Source.id)
        return

    bot.SendMessage(Type, target, img2qr(words, Image), id=Source.id)
