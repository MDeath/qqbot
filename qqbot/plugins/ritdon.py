import os
import requests, time

import soup
from admin import admin_ID
from common import JsonDict, JsonDump, JsonLoad
from qqbotcls import QQBotSched

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'Origin': 'http://ritdon.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.81 Safari/537.36 Edg/104.0.1293.47',
}

cookies = {
    'ST0N_2132_nofavfid': '1',
    'ST0N_2132_saltkey': 'mZ71ICQ6',
    'ST0N_2132_lastvisit': '1659960974',
    'ST0N_2132_auth': 'c982ztLTfY0owqOtH8lSDNbYgtbi5A9a1URWAFPXRSKFt%2FjJBnCYvd308r5dtqeUxw8PqiuaF%2Fc%2FBBCuOPTiBzEK4w',
    'ST0N_2132_lastcheckfeed': '23067%7C1659964579',
    'ST0N_2132_home_readfeed': '1659964680',
    'ST0N_2132_atarget': '1',
    'ST0N_2132_smile': '1D1',
    'ST0N_2132_ulastactivity': 'e0c1vP%2B7F6jtR%2BL5f2a0rmbvGYGLKGTUvRlRq%2BAK%2BfMHBM4UC5tb',
    'ST0N_2132_st_t': '23067%7C1660063227%7C7d31d9523e805c3d9ccdd8367332058d',
    'ST0N_2132_forum_lastvisit': 'D_40_1659964753D_49_1660063227',
    'ST0N_2132_visitedfid': '49D40D45',
    'ST0N_2132_viewid': 'tid_10547',
    'ST0N_2132_st_p': '23067%7C1660063236%7C0a4666c665eec3af2c73ae1af8ce5daa',
    'ST0N_2132_home_diymode': '1',
    'ST0N_2132_sid': 'kjJodO',
    'ST0N_2132_lip': '59.42.116.63%2C1660064633',
    'ST0N_2132_sendmail': '1',
    'ST0N_2132_lastact': '1660065319%09home.php%09editor',
}

def cookies():
    return {
    'ST0N_2132_saltkey': 'mZ71ICQ6',
    'ST0N_2132_lastvisit': '1659960974', # 上次访问
    'ST0N_2132_atarget': '1',
    'ST0N_2132_smile': '1D1',
    'ST0N_2132_auth': 'c982ztLTfY0owqOtH8lSDNbYgtbi5A9a1URWAFPXRSKFt%2FjJBnCYvd308r5dtqeUxw8PqiuaF%2Fc%2FBBCuOPTiBzEK4w',
    'ST0N_2132_lastcheckfeed': f'23067%7C{int(time.time())}', # 上次主动验证
    'ST0N_2132_nofavfid': '1',
    'ST0N_2132_ulastactivity': '2d5fngW%2B96anR6rDwdljFUpVq32x5AKjCTZYAli8Nn0ndvYwOORh',
    'ST0N_2132_st_t': f'23067%7C{int(time.time())}%7Ce76a995c074935781281800e8c635c63',
    'ST0N_2132_forum_lastvisit': f'D_40_{int(time.time())}D_49_{int(time.time())}', #  最后一次访问论坛
    'ST0N_2132_visitedfid': '49D45D40',
    'ST0N_2132_st_p': f'23067%7C{int(time.time())}%7C42341c1d9d5c59ae1916f5e3f3ae53a0',
    'ST0N_2132_space_top_friendnum_23067': '1',
    'ST0N_2132_home_diymode': '0',
    'ST0N_2132_sid': 'usPUXQ',
    'ST0N_2132_lip': f'113.65.250.188%2C{int(time.time())}',
    'ST0N_2132_viewid': 'uid_23067',
}

def onPlug(bot):
    '''\
    深夜图书馆'''
    try:
        if os.path.exists(bot.conf.Config('ritdon.json')):
            with open(bot.conf.Config('ritdon.json'), 'r', encoding='utf-8') as f:bot.ritdon = JsonLoad(f)
        else:raise
    except:
        bot.ritdon = JsonDict(last_member_id=1,error=None)
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)
    
def onUnplug(bot):
    if hasattr(bot,'ritdon'):delattr(bot,'ritdon')

def onInterval(bot):
    with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)

def ritdon_log_sched(bot):
    hd = headers.copy()
    hd['Cache-Control'] = 'no-cache'
    hd['Content-Type'] = 'multipart/form-data; boundary=----WebKitFormBoundaryTIR2OVTAfBkcbCrE'
    hd['Pragma'] = 'no-cache'
    hd['Referer'] = 'http://ritdon.com/home.php?mod=spacecp&ac=blog'

    ck = cookies()
    ck['ST0N_2132_home_readfeed'] = str(int(time.time()))
    ck['ST0N_2132_lastact'] = f'{int(time.time())}%09home.php%09editor'

    params = {
        'mod': 'spacecp',
        'ac': 'blog',
        'blogid': '',
    }

    data = '''------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="subject"


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="savealbumid"

0
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="newalbum"

请输入相册名称
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="file"; filename=""
Content-Type: application/octet-stream


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="file"; filename=""
Content-Type: application/octet-stream


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="message"

%s
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="classid"

0
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="tag"


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="friend"

0
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="password"


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="selectgroup"


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="target_names"


------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="blogsubmit"

true
------WebKitFormBoundaryTIR2OVTAfBkcbCrE
Content-Disposition: form-data; name="formhash"

4f713c23
------WebKitFormBoundaryTIR2OVTAfBkcbCrE--
'''

    context = f'标题:レイン・パターソン&nbsp;Pid:100259704<br>作者:lack&nbsp;Uid:83739<br>时间:2022-08-06T00:00:18+09:00<br>类型:illust&nbsp;收藏:20375&nbsp;标签:<br>にじさんじ:彩虹社<br>バーチャルYouTuber:虚拟主播<br>レイン・パターソン:Lain&nbsp;Paterson<br>バーチャルYouTuber10000users入り:Virtual&nbsp;YouTuber&nbsp;10000+&nbsp;bookmarks<div><p><a href="https://i.pixiv.re/img-original/img/2022/08/06/00/00/18/100259704_p0.png" target="_blank"><img src="https://i.pixiv.re/img-original/img/2022/08/06/00/00/18/100259704_p0.png"></a></p></div>'

    response = requests.post('http://ritdon.com/home.php', params=params, cookies=ck, headers=hd, data=(data % context).encode('utf-8'), verify=False)
    print(response.text)

@QQBotSched(minute=0)
def last_member_id(bot):
    if not hasattr(bot, 'ritdon'):return

    hd = headers.copy()
    hd['Cache-Control'] = 'max-age=0'
    hd['Content-Type'] = 'application/x-www-form-urlencoded'
    hd['Referer'] = 'http://ritdon.com/'

    ck = cookies()
    ck['ST0N_2132_extstyle'] = './template/default/style/t5'
    ck['ST0N_2132_sendmail'] = '1'
    ck['ST0N_2132_widthauto'] = '1'
    ck['ST0N_2132_noticeTitle'] = '1'
    ck['ST0N_2132_promptstate_23067'] = '0'
    ck['Hm_lvt_a284ebcdec513778ddb631756ecf94f3'] = str(int(time.time()))
    ck['ST0N_2132_viewid'] = f'uid_{bot.ritdon.last_member_id}'
    ck['ST0N_2132_lastact'] = f'{int(time.time())}%09home.php%09spacecp'
        
    data = {
    'referer': f'http://ritdon.com/home.php?mod=space&uid={bot.ritdon.last_member_id}',
    'addsubmit': 'true',
    'handlekey': f'a_friend_li_{bot.ritdon.last_member_id}',
    'formhash': '7b1094ad', # auth?
    'note': '', # 验证信息
    'gid': '1'
    }

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

    try:response = requests.get('http://ritdon.com/home.php', params=params, cookies=ck, verify=False)
    except:pass
    if '抱歉，您指定的用户空间不存在' in response.text:
        return
    elif '正在等待验证' in response.text:
        bot.ritdon.last_member_id += 1
    elif '你们已成为好友' in response.text:
        bot.ritdon.last_member_id += 1
    elif '抱歉，您不能加自己为好友' in response.text:
        bot.ritdon.last_member_id += 1
    elif f'<em id="return_a_friend_li_2">加为好友</em>' in response.text:
        params = {
            'mod': 'spacecp',
            'ac': 'friend',
            'op': 'add',
            'uid': str(bot.ritdon.last_member_id),
            'inajax': '1',
        }
        response = requests.post('http://ritdon.com/home.php', params=params, cookies=cookies, data=data, verify=False)
        for f in admin_ID():
            bot.SendMessage('Friend', f, soup.Plain(f'ritdon {bot.ritdon.last_member_id} 加为好友'))
        bot.ritdon.last_member_id += 1
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)
    elif f'<em id="return_a_friend_li_2">批准请求</em>' in response.text:
        params = {
            'mod': 'spacecp',
            'ac': 'friend',
            'op': 'add',
            'uid': str(bot.ritdon.last_member_id),
            'inajax': '1',
        }
        response = requests.post('http://ritdon.com/home.php', headers=hd, params=params, cookies=cookies, data=data, verify=False)
        for f in admin_ID():
            bot.SendMessage('Friend', f, soup.Plain(f'ritdon {bot.ritdon.last_member_id} 批准请求'))
        bot.ritdon.last_member_id += 1
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)
    else:
        for f in admin_ID():
            bot.SendMessage('Friend', f, soup.Plain(f'ritdon {bot.ritdon.last_member_id} 添加失败 $print(bot.ritdon.error)'))
        bot.ritdon.error = response.text
        with open(bot.conf.Config('ritdon.json'),'w', encoding='utf-8') as f:JsonDump(bot.ritdon, f, indent=4)
        return

