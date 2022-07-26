import os
import requests, time

import soup
from admin import admin_ID
from common import JsonDict, JsonDump, JsonLoad
from qqbotcls import QQBotSched

headers = {
    'Connection': 'keep-alive',
    'Cache-Control': 'max-age=0',
    'Upgrade-Insecure-Requests': '1',
    'Origin': 'http://ritdon.com',
    'Content-Type': 'application/x-www-form-urlencoded',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.43',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Referer': 'http://ritdon.com/home.php?mod=space&uid=1&do=index',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
}

cookies = {
    'ST0N_2132_saltkey': 'svYf0D77',
    'ST0N_2132_lastvisit': '1638517785',
    'ST0N_2132_atarget': '1',
    'ST0N_2132_extstyle': './template/default/style/t5',
    'ST0N_2132_promptstate_23067': '0',
    'ST0N_2132_smile': '4D1',
    'ST0N_2132_auth': '1689byXLiuED%2B0XkqqvcKfX9B%2BNTg9Nd0%2FwH3tgHU2qXLCsW94kqf8B%2F5gxpbAm0yITilr2Cu%2Bxi8pAjvNDrFolepA',
    'ST0N_2132_lastcheckfeed': '23067%7C1639193353',
    'ST0N_2132_nofavfid': '1',
    'Hm_lvt_a284ebcdec513778ddb631756ecf94f3': '1639708099',
    'ST0N_2132_widthauto': '1',
    'ST0N_2132_ulastactivity': '5f7fn9tojtaWNfrdhikX%2BfAInvOmVm4dAuCQbAuT0%2B6gz8lDSwwg',
    'ST0N_2132_st_t': '23067%7C1640229455%7Ce76a995c074935781281800e8c635c63',
    'ST0N_2132_forum_lastvisit': 'D_53_1639366275D_48_1639366617D_67_1639366942D_2_1639369955D_46_1639472244D_39_1639474084D_45_1640229388D_40_1640229455',
    'ST0N_2132_visitedfid': '40D45D39D2D46D67D48D53D49',
    'ST0N_2132_st_p': '23067%7C1640229464%7C42341c1d9d5c59ae1916f5e3f3ae53a0',
    'ST0N_2132_space_top_friendnum_23067': '14',
    'ST0N_2132_home_diymode': '1',
    'ST0N_2132_sid': 'usPUXQ',
    'ST0N_2132_lip': '113.65.250.188%2C1640247141',
    'ST0N_2132_noticeTitle': '1',
    'ST0N_2132_sendmail': '1',
    'ST0N_2132_viewid': 'uid_23329',
}

data = {
  'referer': 'http://ritdon.com/home.php?mod=space&uid=1',
  'addsubmit': 'true',
  'handlekey': 'a_friend_li_1',
  'formhash': '7b1094ad', # auth?
  'note': '', # 验证信息
  'gid': '1'
}

def onPlug(bot):
    try:
        if os.path.exists(bot.conf.Config('ritdon.json')):
            with open(bot.conf.Config('ritdon.json'), 'r', encoding='utf-8') as f:bot.ritdon = JsonLoad(f)
        else:raise
    except:
        bot.ritdon = JsonDict(last_member_id = 1)
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)

def onInterval(bot):
    with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)

@QQBotSched(hour=6)
def ritdon_log_sched(bot):
    pass

@QQBotSched(second=0)
def last_member_id(bot):
    if not hasattr(bot, 'ritdon'):return
    cookies['ST0N_2132_viewid'] = f'uid_{bot.ritdon.last_member_id}'
    cookies['ST0N_2132_lastact'] = f'{int(time.time())}%09home.php%09spacecp'
    data['referer'] = f'http://ritdon.com/home.php?mod=space&uid={bot.ritdon.last_member_id}'
    data['handlekey'] = f'a_friend_li_{bot.ritdon.last_member_id}'
    params = {
        'mod': 'spacecp',
        'ac': 'friend',
        'op': 'add',
        'uid': str(bot.ritdon.last_member_id),
        'handlekey': ['addfriendhk_2', 'a_friend_li_2'],
        'infloat': 'yes',
        'inajax': '1',
        'ajaxtarget': 'fwin_content_a_friend_li_2',
    }
    try:response = requests.get('http://ritdon.com/home.php', params=params, cookies=cookies, verify=False)
    except:pass
    if '抱歉，您指定的用户空间不存在' in response.text:
        return
    if '正在等待验证' in response.text:
        bot.ritdon.last_member_id += 1
    if '你们已成为好友' in response.text:
        bot.ritdon.last_member_id += 1
    if '抱歉，您不能加自己为好友' in response.text:
        bot.ritdon.last_member_id += 1
    if f'<em id="return_a_friend_li_2">加为好友</em>' in response.text:
        params = {
            'mod': 'spacecp',
            'ac': 'friend',
            'op': 'add',
            'uid': str(bot.ritdon.last_member_id),
            'inajax': '1',
        }
        response = requests.post('http://ritdon.com/home.php', params=params, cookies=cookies, data=data, verify=False)
        for f in bot.Friend:
            if admin_ID(bot, f.id):
                bot.SendMessage('Friend', f.id, soup.Plain(f'{bot.ritdon.last_member_id} 加为好友'))
        bot.ritdon.last_member_id += 1
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)
    if f'<em id="return_a_friend_li_2">批准请求</em>' in response.text:
        params = {
            'mod': 'spacecp',
            'ac': 'friend',
            'op': 'add',
            'uid': str(bot.ritdon.last_member_id),
            'inajax': '1',
        }
        response = requests.post('http://ritdon.com/home.php', headers=headers, params=params, cookies=cookies, data=data, verify=False)
        for f in bot.Friend:
            if admin_ID(bot, f.id):
                bot.SendMessage('Friend', f.id, soup.Plain(f'{bot.ritdon.last_member_id} 批准请求'))
        bot.ritdon.last_member_id += 1
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)