
import imageio, io, jieba, time, wordcloud

import soup
from qqbotcls import QQBotSched,bot
from qdb import DataObj

# WordCloud 参数配置解释
# 字体路径。用于指定生成词云时使用的字体文件。这对于正确显示非英文字符非常重要。
FONT_PATH: str |  None = r"C:\Windows\Fonts\msyhbd.ttc"

# 词云的宽度（以像素为单位）。这个参数决定了生成词云图像的宽度。
WIDTH: int = 2048

# 词云的高度（以像素为单位）。这个参数决定了生成词云图像的高度。
HEIGHT: int = 2048

# 词云图像边缘的空白宽度（以像素为单位）。较大的值会在词云周围留下更多的空白。
MARGIN: int = 1

# 如果设置为True或某个整数n，则只考虑最常见的n个单词（或所有单词，如果True），忽略其他单词的频率。
RANKS_ONLY: int | bool | None = None

# 控制生成词云时单词更倾向于水平还是垂直放置的比例。值越接近1，单词越倾向于水平放置。
PREFER_HORIZONTAL: float = .9

# 用于生成词云的掩码图像。如果提供了掩码，词云将只在掩码的非白色区域生成。这对于创建特定形状的词云非常有用。
MASK = imageio.imread(bot.conf.Config('wordclouds/delisha_mask.png'))

# 控制词云中单词的大小比例。较大的值会使所有单词变大，但不影响单词之间的相对大小。
SCALE: int = 1

# 一个函数，用于生成每个单词的颜色。如果提供，它将覆盖colormap参数。
COLOR_FUNC: None = None

# 词云中显示的最大单词数。
MAX_WORDS: int = 2000

# 词云中显示单词的最小字体大小。
MIN_FONT_SIZE: int = 4

# 一个集合或列表，包含不应包含在词云中的单词（停用词）。
with open(bot.conf.Config('wordclouds/stopwords.txt'), 'r', encoding='utf-8') as f:\
STOPWORDS: list | None = f.read().splitlines()

# 控制生成词云的随机性。如果提供，则结果将是可重复的。
RANDOM_STATE: int | None = None

# 词云的背景颜色。
BACKGROUND_COLOR: str = 'rgba(255,255,255,0)'

# 词云中显示单词的最大字体大小。如果未设置，则根据其他参数自动确定。
MAX_FONT_SIZE: int | None = None

# 字体大小的增量步长。这决定了词云中相邻单词之间的字体大小差异。
FONT_STEP: int = 1

# 生成词云图像的模式。通常是"RGB"或"RGBA"（包含透明度）。
MODE: str = "RGBA"

# 控制单词之间相对大小的方式。'auto'表示根据单词频率自动调整大小。
RELATIVE_SCALING: str = 'auto'

# 一个正则表达式，用于从文本中提取单词。如果提供，它将覆盖默认的单词提取逻辑。
REGEXP: str | None = None

# 是否考虑单词的共现（即相邻出现的单词）。这有助于在词云中更紧密地聚集相关单词。
COLLOCATIONS: bool = True

# 用于生成词云中单词颜色的颜色映射（调色板）。如果提供，它将覆盖color_func参数。
COLORMAP: None = 'hsv'

# 是否将单词的复数形式归一化为单数形式。这有助于在词云中减少重复单词的数量。
NORMALIZE_PLURALS: bool = True

# 词云轮廓的宽度（以像素为单位）。较大的值会在词云周围生成更宽的轮廓。
CONTOUR_WIDTH: int = 0

# 词云轮廓的颜色。
CONTOUR_COLOR: str = 'BLACK'

# 是否重复整个生成过程，以尝试获得更好的布局。这可能会增加生成词云所需的时间。
REPEAT: bool = True

# 是否在词云中包含数字。
INCLUDE_NUMBERS: bool = False

# 词云中单词的最小长度（以字符为单位）。较短的单词将被忽略。
MIN_WORD_LENGTH: int = 0

# 确定两个单词是否被视为共现的阈值。如果两个单词在文本中相邻出现的次数超过此阈值，则它们将被视为共现。
COLLOCATION_THRESHOLD: int = 30

def WordCloud(text:str | list):
    for k, v in __import__(__name__).__dict__.items():
        if k.isupper():
            globals()[k] = v
    if not isinstance(text, str):
        text = ' '.join([str(t) for t in text])
    wc = wordcloud.WordCloud(
        font_path=FONT_PATH, 
        width=WIDTH, 
        height=HEIGHT, 
        margin=MARGIN,
        ranks_only=RANKS_ONLY, 
        prefer_horizontal=PREFER_HORIZONTAL, 
        mask=MASK, 
        scale=SCALE,
        color_func=COLOR_FUNC, 
        max_words=MAX_WORDS, 
        min_font_size=MIN_FONT_SIZE,
        stopwords=STOPWORDS, 
        random_state=RANDOM_STATE, 
        background_color=BACKGROUND_COLOR,
        max_font_size=MAX_FONT_SIZE, 
        font_step=FONT_STEP, 
        mode=MODE,
        relative_scaling=RELATIVE_SCALING, 
        regexp=REGEXP, 
        collocations=COLLOCATIONS,
        colormap=COLORMAP, 
        normalize_plurals=NORMALIZE_PLURALS, 
        contour_width=CONTOUR_WIDTH,
        contour_color=CONTOUR_COLOR, 
        repeat=REPEAT,
        include_numbers=INCLUDE_NUMBERS, 
        min_word_length=MIN_WORD_LENGTH, 
        collocation_threshold=COLLOCATION_THRESHOLD
    ).generate(' '.join(jieba.lcut(text)))
    img_stream = io.BytesIO()
    wc.to_image().save(img_stream, format='PNG')
    return soup.Image(img_stream.getvalue())
    

class wordclouds(DataObj): # 注册表数据对象
    columns = '''\
id          INTEGER     PRIMARY KEY     NOT NULL,
time        INTEGER     NOT NULL,
type        TEXT        NOT NULL,
target      INTEGER,
sender      INTEGER     NOT NULL,
content     TEXT
'''

def onPlug(bot):
    bot.db.Add_Tabel_DataObj(wordclouds)

@QQBotSched(hour=0)
def Day(bot,date:str=None):
    '每日任务'
    if date:timestamp = time.mktime(time.strptime(date,'%Y%m%d'))
    else:timestamp = time.mktime(time.localtime())-24*60*60
    st2et = f'({int(timestamp)+24*60*60} > time and time >= {int(timestamp)})'
    for Type,name,target in [('group',g.group_name,g.group_id) for g in bot.Group()]+[('friend',f,f.user_id) for f in bot.Friend()]:
        text = [t.content for t in bot.db.Select('wordclouds', f'type="{Type}" and target={target} and {st2et}')]
        if not text:continue
        wc = WordCloud(text)
        if Type == 'group':bot.SendMsg(Type,target,soup.Text(f'昨日群词云'),wc)
        else:
            for f in bot.Friend(remark='Admin'):
                bot.SendMsg('friend',f.user_id,soup.Text(f'{Type}:{name}({target})'),wc)

@QQBotSched(day_of_week=0)
def Week(bot,date:str=None):
    '每周任务'
    if date:timestamp = time.mktime(time.strptime(date,'%Y%m%d'))
    else:timestamp = time.mktime(time.localtime())-7*24*60*60
    st2et = f'({int(timestamp)+7*24*60*60} > time and time >= {int(timestamp)})'
    for Type,name,target in [('group',g.group_name,g.group_id) for g in bot.Group()]+[('friend',f,f.user_id) for f in bot.Friend()]:
        text = [t.content for t in bot.db.Select('wordclouds', f'type="{Type}" and target={target} and {st2et}')]
        if not text:continue
        wc = WordCloud(text)
        if Type == 'group':bot.SendMsg(Type,target,soup.Text(f'上周群词云'),wc)
        else:
            for f in bot.Friend(remark='Admin'):
                bot.SendMsg('friend',f.user_id,soup.Text(f'{Type}:{name}({target})'),wc)

@QQBotSched(day=1)
def Month(bot,date:str=None):
    '每月任务'
    if date:
        struct_time = time.strptime(date,'%Y%m%d')
        start_time = time.mktime(struct_time)
        end_time = time.mktime(struct_time[:1]+[struct_time.tm_mon+1]+struct_time[2:])
    else:
        struct_time = time.localtime()
        if struct_time.tm_mon == 1:
            start_time = time.mktime([struct_time.tm_year-1]+[12]+struct_time[2:])
            end_time = time.mktime(struct_time)
        else:
            start_time = time.mktime(struct_time[:1]+[struct_time.tm_mon-1]+struct_time[2:])
            end_time = time.mktime(struct_time)
    st2et = f'({int(start_time)} > time and time >= {int(end_time)})'
    for Type,name,target in [('group',g.group_name,g.group_id) for g in bot.Group()]+[('friend',f,f.user_id) for f in bot.Friend()]:
        text = [t.content for t in bot.db.Select('wordclouds', f'type="{Type}" and target={target} and {st2et}')]
        if not text:continue
        wc = WordCloud(text)
        if Type == 'group':bot.SendMsg(Type,target,soup.Text(f'上月群词云'),wc)
        else:
            for f in bot.Friend(remark='Admin'):
                bot.SendMsg('friend',f.user_id,soup.Text(f'{Type}:{name}({target})'),wc)

def onQQMessage(bot, Type, Sender, Source, Message):
    Text = ''
    for msg in Message:
        if msg.type == 'text':Text += msg.text
    if Text:bot.db.Insert('wordclouds', [Source.message_id, Source.time, Type, Source.target, Sender.user_id, Text])