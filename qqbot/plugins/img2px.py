import soup
from common import b64enc

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    px + 图片
    像素 + 图片
    生成像互动素图'''
    Plain = ''
    Image = []
    for msg in Message:
        if msg.type == 'text':Plain += msg.text
        if msg.type == 'image':Image.append(msg)
        if msg.type == 'reply':
            try:Message += [m for m in bot.GetMsg(msg.id).message if m.type == 'image']
            except:pass
    if Plain.strip() not in ['像素','px']:return
    if not Image:
        bot.SendMsg(Type, Source.target, soup.Text('⚠️关联图片失败，请尝试直接和图片一起发送⚠️'), reply=Source.message_id)
        return
    bot.SendMsg(Type, Source.target, soup.Text('\n'.join(['移动端双击拖动后开刮']+['https://koalastothemax.com/?'+b64enc(img.url) for img in Image])), reply=Source.message_id)