import os

def build_all():
    print(">>> 正在生成配置与部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"
    API_SECRET = "MusicDL_SecretKey_2026_Secure"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';
const API_SECRET = '""" + API_SECRET + """';

const CLIENT_SCRIPT = `/**
 * @name MusicDL 核心提取源
 * @description 基于 musicdl 算法移植 (全平台直连版)
 * @version 1.6.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;

send(EVENT_NAMES.inited, {
  status: true,
  openDevTools: false,
  sources: {
    kw: { name: '酷我音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    kg: { name: '酷狗音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    wy: { name: '网易云音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    mg: { name: '咪咕音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] }
  }
});

on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    let songId = musicInfo.songmid || musicInfo.id;
    if (source === 'kg') {
      songId = musicInfo.hash || musicInfo.sqHash || musicInfo.hqHash || musicInfo.songmid || musicInfo.id;
    }

    const apiUrl = WORKER_URL + '/parse?source=' + source + '&id=' + encodeURIComponent(songId) + '&quality=' + quality + '&secret=' + '""" + API_SECRET + """';

    try {
      const res = await request(apiUrl, { method: 'GET', timeout: 10000 });
      const body = typeof res.body === 'string' ? JSON.parse(res.body) : res.body;
      if (body && body.code === 0 && body.url) {
        return body.url;
      }
      throw new Error(body.msg || '无法解析播放地址');
    } catch (err) {
      throw new Error(err.message || '网络请求失败');
    }
  }
});
`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': '*',
      'Cache-Control': 'no-cache'
    };

    if (request.method === 'OPTIONS') return new Response(null, { headers: corsHeaders });

    if (url.pathname === '/lx-source.js') {
      return new Response(CLIENT_SCRIPT, {
        headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' }
      });
    }

    if (url.pathname === '/parse') {
      const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };
      const source = url.searchParams.get('source');
      const songmid = url.searchParams.get('id');
      const secret = url.searchParams.get('secret');

      if (secret !== API_SECRET) {
        return new Response(JSON.stringify({ code: 403, msg: '密钥不匹配' }), { status: 403, headers: jsonHeaders });
      }

      if (!source || !songmid) {
        return new Response(JSON.stringify({ code: 400, msg: '缺少参数' }), { status: 400, headers: jsonHeaders });
      }

      try {
        const musicUrl = await parseMusicDL(source, songmid);
        if (musicUrl) {
          return new Response(JSON.stringify({ code: 0, url: musicUrl }), { headers: jsonHeaders });
        }
        return new Response(JSON.stringify({ code: 404, msg: '解析失败，平台返回空地址' }), { status: 200, headers: jsonHeaders });
      } catch (err) {
        return new Response(JSON.stringify({ code: 500, msg: '解析异常: ' + err.message }), { status: 200, headers: jsonHeaders });
      }
    }

    return new Response('MusicDL Engine Active', { status: 200, headers: corsHeaders });
  }
};

// 移植 musicdl 核心解析接口
async function parseMusicDL(source, songid) {
  // 1. 酷我音乐 (musicdl/modules/sources/kw.py 逻辑移植)
  if (source === 'kw') {
    const targetUrl = `https://antiserver.kuwo.cn/anti.s?type=convert_url&rid=${songid}&format=mp3&response=url`;
    const res = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Referer': 'http://www.kuwo.cn/'
      }
    });
    const urlText = await res.text();
    if (urlText && urlText.startsWith('http')) return urlText;
  }

  // 2. 网易云音乐 (musicdl/modules/sources/netease.py 逻辑移植)
  if (source === 'wy') {
    const targetUrl = `https://music.163.com/api/song/enhance/player/url?ids=[${songid}]&br=320000`;
    const res = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Referer': 'https://music.163.com/',
        'Cookie': 'os=pc; osver=Microsoft-Windows-10-Professional-build-19042-64bit; appver=2.0.3.131777'
      }
    });
    const data = await res.json();
    if (data?.data?.[0]?.url) {
      return data.data[0].url.replace('http://', 'https://');
    }
  }

  // 3. 酷狗音乐 (musicdl/modules/sources/kugou.py 逻辑移植)
  if (source === 'kg') {
    const targetUrl = `https://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash=${songid}`;
    const res = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
      }
    });
    const data = await res.json();
    if (data && data.url) return data.url;
  }

  // 4. 咪咕音乐 (musicdl/modules/sources/migu.py 逻辑移植)
  if (source === 'mg') {
    const targetUrl = `https://c.musicquery.migu.cn/v1.0/content/share_new.do?contentId=${songid}&contenttype=1`;
    const res = await fetch(targetUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)',
        'channel': '0146951'
      }
    });
    const data = await res.json();
    if (data?.info?.url) return data.info.url;
  }

  return '';
}
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> 文件生成成功！")

if __name__ == "__main__":
    build_all()
