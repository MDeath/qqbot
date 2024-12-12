# %%
import html, random, re, requests, uuid
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
def wyptb_stats(ogid:int,ass):
    response = requests.get(f'{WYPTB}{ogid}/{ass}')
    response = requests.get(f'{WYPTB}{ogid}/stats')
    if response.url == WYPTB:raise
    Pressed, Didntpress = re.findall(r'(\d+ \(\d+%\))<', response.text)
    return ogid, Pressed, Didntpress

# %%
TABLE = {}
def onQQMessage(bot, Type, Sender, Source, Message):
    '''\
    按或不按
    yes or no'''
    Text = ''.join([msg.text for msg in Message if msg.type == 'text'])
    if Text.strip().lower() in ['按或不按', 'yes or no']:
        ogid, cond, res = wyptb()
        cond, res = translate(cond, res)
        TABLE[Source.target] = {'ogid':ogid, 'cond':cond, 'res':res}
        bot.SendMsg(Type,Source.target, soup.Text('\n'.join([cond, '但是', res, '按(yes) 或 不按(no)'])))
    elif Source.target in TABLE and Text.strip().lower() in ['按','不按','yes','no']:
        ogid, cond, res = TABLE.pop(Source.target).values()
        ogid, Pressed, Didntpress = wyptb_stats(ogid, 'yes' if Text.strip().lower() in ['按','yes'] else 'no')
        bot.SendMsg(Type,Source.target, soup.Text('\n'.join(['以按下按钮' if Text.strip().lower() in ['按','yes'] else '没按下按钮', cond, '但是', res, f'{Pressed}人选择按下', f'{Didntpress}人选择不按'])))

# %%
if __name__ == '__main__':
    response = requests.get(WYPTB)
    ogid = int(re.findall(r'com/(\d+)"', response.text)[0])
    ogid, cond, res, Pressed, Didntpress = wyptb()
    print(ogid, cond, 'but', res, '\n', *translate(cond, 'but', res))
    print(f'{Pressed}人选择按下\n{Didntpress}人选择不按')