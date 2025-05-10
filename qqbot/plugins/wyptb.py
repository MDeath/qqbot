# %%
import html, re, requests, uuid
# %%
import soup
# %%
WYPTB = 'https://willyoupressthebutton.com/'
ENDPOINT = "https://api.cognitive.microsofttranslator.com"
LOCATION = "eastasia"
KEY = "8I7aQdyYt9XBUvZHt2m86FPhVJ46tthv27Pp4aZZGFaTMUE8izrzJQQJ99AKAC3pKaRXJ3w3AAAbACOGp8pU"

# %%
def translate(*text:str, to=[['zh-Hans']]):
    path = '/translate'
    constructed_url = ENDPOINT + path
    params = {'api-version': '3.0','to': to}
    headers = {'Ocp-Apim-Subscription-Key': KEY,'Ocp-Apim-Subscription-Region': LOCATION,'Content-type': 'application/json','X-ClientTraceId': str(uuid.uuid4())}
    body = [{'text': t} for t in text]
    request = requests.post(constructed_url, params=params, headers=headers, json=body).json()
    return [t['translations'][0]['text'] for t in request]
    
# %%
def wyptb():
    response = requests.get(WYPTB)
    ogid = int(re.findall(r'com/(\d+)"', response.text)[0])
    cond, res = re.findall(r'<div class="rect" id=".*?">(.*?)</div>', html.unescape(response.text))
    return ogid, cond, res
# %%
def wyptb_stats(ogid:int,ass=None):
    if ass:requests.get(f'{WYPTB}{ogid}/{ass}')
    response = requests.get(f'{WYPTB}{ogid}/stats')
    if response.url == WYPTB:raise
    Pressed, Didntpress = re.findall(r'(\d+ \(\d+%\))<', response.text)
    return Pressed, Didntpress

# %%
TABLE = []

def onInterval(bot):
    for og in TABLE:
        og['count'] += 1
        if og['count'] < 2:continue
        Pressed, Didntpress = wyptb_stats(og['ogid'])
        bot.SendMsg(og['type'],og['target'],soup.Text('\n'.join([og['war_cond'], og['cond'], 'or', '但是', og['war_res'], og['res'] if og['type'] == 'group' else f'{og["res"]}\n按(yes) 或 不按(no)', '全球', f'{Pressed}人选择按下', f'{Didntpress}人选择不按'])))
        if og['type'] == 'group':
            yes = [m.nickname for m in bot.Member(group_id=og['target']) if m.user_id in og['yes'] and m.user_id != bot.qq]
            no = [m.nickname for m in bot.Member(group_id=og['target']) if m.user_id in og['no'] and m.user_id != bot.qq and m.user_id not in og['yes']]
            yes = len(yes), '\n'.join(yes)
            no = len(no), '\n'.join(no)
            bot.SendMsg(og['type'],og['target'],soup.Text(f'有 {yes[0]} 人选择了按下'),soup.Face(424),soup.Text(f':\n{yes[1]}\n'),soup.Text(f'有 {no[0]} 人选择了不按'),soup.Face(123),soup.Text(f':\n{no[1]}'))
    new = [og for og in TABLE if og['count'] < 2]
    TABLE.clear()
    for og in new:TABLE.append(og)

def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    按或不 按
    yes or no'''
    Reply = None
    Text = ''
    for msg in Message:
        if msg.type == 'text':Text += msg.text
        if msg.type == 'reply':Reply = msg.id
    if Text.strip().lower() in ['按不按', '按或不按', 'yes or no']:
        ogid, war_cond, war_res = wyptb()
        cond, res = translate(war_cond, war_res)
        message_id = bot.SendMsg(Type,Source.target, soup.Text('\n'.join([war_cond, cond, 'or', '但是', war_res, res if Type == 'group' else f'{res}\n按(yes) 或 不按(no)']))).message_id
        if Type == 'group':
            while True:
                if bot.Reaction(Source.target, message_id, 424) is not None:continue
                if bot.Reaction(Source.target, message_id, 123) is not None:continue
                break
        TABLE.append({'ogid':ogid, 'war_cond':war_cond, 'war_res':war_res, 'cond':cond, 'res':res, 'yes':set(), 'no':set(), 'other':{}, 'count':0, 'type':Type, 'target':Source.target, 'message_id':message_id})
        
    if Source.target in TABLE and Text.strip().lower() in ['按','不按','yes','no'] and Type != 'group' and Reply is not None:
        for og in range(len(TABLE)):
            if Reply == TABLE[og]['message_id']:break
        og = TABLE.pop(og)
        Pressed, Didntpress = wyptb_stats(og['ogid'], 'yes' if Text.strip().lower() in ['按','yes'] else 'no')
        bot.SendMsg(Type,Source.target, soup.Text('\n'.join(['以按下按钮' if Text.strip().lower() in ['按','yes'] else '没按下按钮', og['war_cond'], og['cond'], 'or', '但是', og['war_res'], og['res'] if Type == 'group' else f'{og["res"]}\n按(yes) 或 不按(no)', f'{Pressed}人选择按下', f'{Didntpress}人选择不按'])))

def onQQNotice(bot, Notice):
    if Notice.notice_type == 'reaction': # 群消息反应
        # time          | int | -               | 事件发生的时间戳
        # self_id       | int | -               | 收到事件的机器人 QQ 号
        # post_type     | str | `notice`        | 上报类型
        # notice_type   | str | `reaction`      | 消息类型
        # sub_type      | str | `add`、`remove` | 提示类型
        # group_id      | int | -               | 群号
        # message_id    | int | -               | 反应的消息 ID
        # operator_id   | int | -               | 操作者 QQ 号
        # code          | str | -               | 表情 ID
        # count         | int | -               | 当前反应数量
        for og in TABLE:
            if Notice.message_id == og['message_id']:
                break
        else:
            return
        if Notice.code == '424' and Notice.sub_type == 'add':og['yes'].add(Notice['operator_id'])
        elif Notice.code == '123' and Notice.sub_type == 'add':og['no'].add(Notice['operator_id'])
        elif Notice.code == '424' and Notice.sub_type == 'remove':og['yes'].remove(Notice['operator_id'])
        elif Notice.code == '123' and Notice.sub_type == 'remove':og['no'].remove(Notice['operator_id'])
        else:og['other'][Notice.code] = Notice['count']

# %%
if __name__ == '__main__':
    response = requests.get(WYPTB)
    ogid = int(re.findall(r'com/(\d+)"', response.text)[0])
    ogid, cond, res, Pressed, Didntpress = wyptb()
    print(ogid, cond, 'but', res, '\n', *translate(cond, 'but', res))
    print(f'{Pressed}人选择按下\n{Didntpress}人选择不按')