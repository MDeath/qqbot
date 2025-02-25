# -*- coding: utf-8 -*-
import cloudscraper, os, time
from amzqr import amzqr

from qqbotcls import bot
from common import JsonDict, b64dec2b
from utf8logger import CRITICAL, DEBUG, ERROR, INFO, PRINT, WARNING
import soup

tempdir = os.path.join(os.getcwd(),'temp','qr')
def get_tempdir():
    temppath = os.path.join(tempdir,time.strftime('%Y%m',time.localtime()))
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

def imageType2qr(message):
    def temp(msg):img2qr(picture=msg)
    soup.Type_Func(message, 'image', temp)

def img2qr(
        word:str=None,
        picture:str|JsonDict=None,
        **kwargs
    ) -> soup.Image:
    '''
    word:文本内容,为空时可以采用picture
    picture:可以是图片对象，本地路径，或是图片url,base64
    或soup.Image和soup.FlashImage(至少包含url)
    '''
    if not (word or picture):raise Exception('wrod or picture 不可同时为空')
    
    file_name, imgurl, byte = time.strftime('%y%m%d%H%M%S',time.localtime()), False, False
    if isinstance(picture, JsonDict):
        if 'url' in picture:imgurl = picture.url
        elif 'file' in picture:
            if picture.file.startswith(('http://','https://')):
                imgurl = picture.file
                if imgurl.endswith(('.jpg','.png','.bmp','.gif')):file_name = imgurl
            elif picture.file.startswith('base64://'):
                try:byte = b64dec2b(picture.file[9:])
                except:Exception('错误的base64')
            else:Exception(f'不支持的格式 {picture.file[:6]}')
        else:Exception('没有包含 url 或 file')

    elif isinstance(picture,str) and picture.startswith('http'):
        imgurl = picture
        if picture.endswith(('.jpg','.png','.bmp','.gif')):
            file_name = picture

    elif picture and os.path.exists(picture):
        with open(picture, 'rb')as f:byte = f.read()

    elif picture:byte = b64dec2b(picture)

    if imgurl and not word:word = imgurl
    elif byte and not word:Exception('字节和Base64图片 word 不得为空')
    
    if imgurl:
        for n in range(5):
            try:byte = cloudscraper.create_scraper().get(imgurl,**kwargs).content
            except Exception as e:pass
            else:break
        else:ERROR(f'{imgurl}\n{e}')
    if byte:
        try:
            if not file_name.endswith(('.jpg','.png','.bmp','.gif')):
                if byte[6:10] in (b'JFIF', b'Exif'):file_name+='.jpg'
                elif byte.startswith(b'\211PNG\r\n\032\n'):file_name+='.png'
                elif byte[:6] in (b'GIF87a', b'GIF89a'):file_name+='.gif'
                elif byte.startswith(b'BM'):file_name+='.bmp'
                else:file_name+='.png'
            picture = os.path.join(get_tempdir(), basename(file_name[-250:]))
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
    return soup.Image(qr_name)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    发送 'qr' 加上 文本
    生成普通QR码
    回复图片发送 'qr'
    生成该图临时QR码
    发送 'qr' 加上 文本 并附带回复 图片
    生成艺术QR码'''
    Plain = ''.join([msg.text for msg in Message if msg.type == 'text']).strip()
    if not Plain.lower().startswith('qr'):return
    Image = None
    for msg in Message:
        if msg.type == 'image':
            Image = msg
            break
        if msg.type == 'reply':
            try:Message += [m for m in bot.GetMsg(msg.id).message if m.type == 'image']
            except:pass
    words = Plain.strip()[2:]

    if not words and not Image:
        bot.SendMsg(Type, Source.target, soup.Text('没有包含文本，或者关联图片，请尝试直接和图片一起发送'), reply=Source.message_id)
        return

    bot.SendMsg(Type, Source.target, img2qr(words, Image), reply=Source.message_id)