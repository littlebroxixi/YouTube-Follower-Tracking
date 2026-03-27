# -*- coding: utf-8 -*-
"""
YouTube Follower Tracking - 数据抓取与摘要生成
    从订阅频道抓取过去24小时的新视频字幕，通过 Kimi API 生成中文摘要
    输出 feed.json 供 skill 读取

主要函数
-------------
resolve_channel_id    通过 handle 解析频道 ID（带缓存）
search_channel_id     通过名称搜索频道 ID
get_recent_videos     获取频道最近视频
get_transcript        通过 Supadata 获取字幕
summarize             通过 Kimi API 生成中文摘要
main                  主函数，输出 feed.json

修改记录
----------
* v1.0.0  2026-03-27  初始版本

作者
-------
YouTube Follower Tracking Bot
"""
import json
import sys
import datetime as dt
import os
import requests
from openai import OpenAI

# =============================================================================
#                             频道列表
# =============================================================================
CHANNELS = [
    {"name": "海伦子 Hellen",            "handle": "hailunzihellen"},
    {"name": "硅谷101播客",               "handle": "valley101podcast"},
    {"name": "美投讲美股",                "handle": "MeiTouJun"},
    {"name": "美股先锋",                  "handle": "meiguxianfeng"},
    {"name": "美股博士",                  "handle": "meiguboshi"},
    {"name": "老石谈芯",                  "handle": "laoshi_tec"},
    {"name": "股市咖啡屋 Stock Cafe",     "handle": "StockCafe"},
    {"name": "视野环球财经",               "handle": "RhinoFinance"},
    {"name": "LEI",                      "handle": "TheMarketMemo"},
    {"name": "PowerUpGammas",            "handle": "PowerUpGammas"},
    {"name": "Sober 聊期权 CFA",          "handle": "Sober66666"},
    {"name": "SpaceX",                   "handle": "SpaceX"},
    {"name": "一口新饭",                  "handle": "MoneyXYZ"},
    {"name": "华尔街阿宝",                "handle": "stock_chat"},
    {"name": "富翁電視 MTTV",             "handle": "mttv"},
    {"name": "小Lin说",                   "handle": "xiao_lin_shuo"},
    {"name": "小岛大浪吹",                "handle": "xiaodaodalang"},
    {"name": "投资TALK君",                "handle": "yttalkjun"},
    {"name": "BWB - Business With Brian","handle": "BusinessWithBrian"},
    {"name": "猴哥财经 HG Finance",       "handle": ""},
    {"name": "美股查理",                  "handle": ""},
    {"name": "美投侃新闻",                "handle": ""},
    {"name": "Nick 美股咖啡館",           "handle": ""},
    {"name": "Terry Chen 泰瑞",          "handle": ""},
    {"name": "Couch Investor",           "handle": ""},
    {"name": "Future Investing",         "handle": ""},
    {"name": "美股投资网",                "handle": ""},
]

# =============================================================================
#                             参数配置
# =============================================================================
HOURS_LOOKBACK = 24
MAX_VIDEOS_PER_CHANNEL = 2
TRANSCRIPT_MAX_CHARS = 50000
CACHE_PATH = os.path.join(os.path.dirname(__file__), 'channel_id_cache.json')
FEED_PATH = os.path.join(os.path.dirname(__file__), 'feed.json')


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH) as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def resolve_channel_id(handle, api_key, cache):
    '''  通过 handle 解析频道 ID，优先读缓存  '''
    if handle in cache:
        return cache[handle]
    url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {'part': 'id', 'forHandle': handle, 'key': api_key}
    resp = requests.get(url, params=params, timeout=10)
    items = resp.json().get('items', [])
    if items:
        channel_id = items[0]['id']
        cache[handle] = channel_id
        return channel_id
    return None


def search_channel_id(name, api_key, cache):
    '''  通过频道名称搜索频道 ID  '''
    cache_key = f'search:{name}'
    if cache_key in cache:
        return cache[cache_key]
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {'part': 'snippet', 'q': name, 'type': 'channel', 'maxResults': 1, 'key': api_key}
    resp = requests.get(url, params=params, timeout=10)
    items = resp.json().get('items', [])
    if items:
        channel_id = items[0]['snippet']['channelId']
        cache[cache_key] = channel_id
        return channel_id
    return None


def get_recent_videos(channel_id, api_key):
    '''  获取频道最近 N 小时内的视频  '''
    published_after = (dt.datetime.utcnow() - dt.timedelta(hours=HOURS_LOOKBACK)).strftime('%Y-%m-%dT%H:%M:%SZ')
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'channelId': channel_id,
        'publishedAfter': published_after,
        'type': 'video',
        'order': 'date',
        'maxResults': MAX_VIDEOS_PER_CHANNEL,
        'key': api_key
    }
    resp = requests.get(url, params=params, timeout=10)
    videos = []
    for item in resp.json().get('items', []):
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        })
    return videos


def get_transcript(video_id, api_key):
    '''  通过 Supadata API 获取视频字幕  '''
    url = 'https://api.supadata.ai/v1/youtube/transcript'
    headers = {'x-api-key': api_key}
    params = {'videoId': video_id, 'text': True}
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 200:
        content = resp.json().get('content', '')
        if isinstance(content, list):
            content = ' '.join(item.get('text', '') for item in content)
        return content[:TRANSCRIPT_MAX_CHARS] if content else None
    return None


def summarize(channel, title, url, transcript, kimi_client):
    '''  通过 Kimi API 生成中文摘要  '''
    prompt = f"""你是一个财经内容分析师，请用中文对以下 YouTube 视频内容进行简洁总结。

频道：{channel}
标题：{title}
链接：{url}

字幕内容：
{transcript}

请输出以下格式：
**核心要点：**
- 要点1（2-3句，说清楚观点和逻辑）
- 要点2
- 要点3
- 要点4
- 要点5（5-7条，每条要有实质内容）

要求：数字、股票代码、涨跌幅等关键数据必须保留原始数值；每条要点要说清楚博主的核心论点和依据，不能只是一句话带过。"""

    resp = kimi_client.chat.completions.create(
        model='kimi-k2.5',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.3
    )
    return resp.choices[0].message.content


def main():
    yt_key = os.environ.get('YOUTUBE_API_KEY', '')
    supa_key = os.environ.get('SUPADATA_API_KEY', '')
    kimi_key = os.environ.get('KIMI_API_KEY', '')

    if not yt_key or not supa_key or not kimi_key:
        print('错误：请设置 YOUTUBE_API_KEY、SUPADATA_API_KEY、KIMI_API_KEY 环境变量', file=sys.stderr)
        sys.exit(1)

    kimi_client = OpenAI(api_key=kimi_key, base_url='https://api.moonshot.cn/v1')
    cache = load_cache()
    videos_output = []

    for ch in CHANNELS:
        name = ch['name']
        handle = ch.get('handle', '').strip()

        if handle:
            channel_id = resolve_channel_id(handle, yt_key, cache)
        else:
            channel_id = search_channel_id(name, yt_key, cache)

        if not channel_id:
            print(f'[跳过] 找不到频道: {name}', file=sys.stderr)
            continue

        videos = get_recent_videos(channel_id, yt_key)
        if not videos:
            continue

        for video in videos:
            transcript = get_transcript(video['video_id'], supa_key)
            if not transcript:
                print(f'[跳过] 无字幕: {video["title"]}', file=sys.stderr)
                continue

            print(f'[摘要] {name} - {video["title"][:40]}', file=sys.stderr)
            summary = summarize(name, video['title'], video['url'], transcript, kimi_client)
            videos_output.append({
                'channel': name,
                'title': video['title'],
                'url': video['url'],
                'summary': summary
            })

    save_cache(cache)

    feed = {
        'generated_at': dt.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'videos': videos_output
    }
    with open(FEED_PATH, 'w', encoding='utf-8') as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f'完成，共处理 {len(videos_output)} 个视频', file=sys.stderr)


if __name__ == '__main__':
    main()
