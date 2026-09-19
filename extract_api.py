import os

def build_all():
    print(">>> 正在生成配置与部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';

const CLIENT_SCRIPT = `/**
 * @name MusicDL 自动化源
 * @description 实时解析音源
 * @version 1.0.0
 */

const { EVENT_NAMES, request, on } = globalThis.lx;

// 1. 响应初始化事件（关键：解决一直显示“初始化中”的问题）
on(EVENT_NAMES.inited, ({ status, openDevTools }) => {
  console.log('MusicDL 自定义源初始化成功！');
});

// 2. 响应音乐 URL 请求
on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    const songId = musicInfo.songmid || musicInfo.id;
    const apiUrl = WORKER_URL + '/?source=' + source + '&id=' + songId + '&quality=' + quality;

    try {
      const res = await request(apiUrl, { method: 'GET', timeout: 8000 });
      const body = typeof res.body === 'string' ? JSON.parse(res.body) : res.body;
      if (body.code === 0 && body.url) return body.url;
      throw new Error(body.msg || '获取播放地址失败');
    } catch (err) {
      throw new Error('接口响应失败: ' + err.message);
    }
  }
});
`;

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    // 跨域头配置
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': '*',
      'Content-Type': 'application/javascript; charset=utf-8'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // 1. 返回客户端源脚本
    if (url.pathname === '/lx-source.js') {
      return new Response(CLIENT_SCRIPT, {
        headers: {
          ...corsHeaders,
          'Content-Type': 'application/javascript; charset=utf-8'
        }
      });
    }

    // 2. 后端 API 解析
    const source = url.searchParams.get('source');
    const songmid = url.searchParams.get('id');
    const quality = url.searchParams.get('quality') || '128k';

    const jsonHeaders = {
      ...corsHeaders,
      'Content-Type': 'application/json; charset=utf-8'
    };

    if (!source || !songmid) {
      return new Response(JSON.stringify({ code: 400, msg: 'Missing source or id' }), { status: 400, headers: jsonHeaders });
    }

    try {
      let musicUrl = '';
      switch (source) {
        case 'kw': musicUrl = await parseKuwo(songmid, quality); break;
        case 'wy': musicUrl = await parseNetease(songmid, quality); break;
        case 'mg': musicUrl = await parseMigu(songmid, quality); break;
        default: return new Response(JSON.stringify({ code: 400, msg: 'Unsupported source' }), { status: 400, headers: jsonHeaders });
      }
      return new Response(JSON.stringify({ code: 0, url: musicUrl }), { headers: jsonHeaders });
    } catch (err) {
      return new Response(JSON.stringify({ code: 500, msg: err.message }), { status: 500, headers: jsonHeaders });
    }
  }
};

async function parseKuwo(rid, quality) {
  const reqUrl = 'https://antiserver.kuwo.cn/anti.s?type=convert_url&rid=' + rid + '&format=mp3&response=url';
  const res = await fetch(reqUrl, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } });
  const text = await res.text();
  if (text && text.startsWith('http')) return text;
  throw new Error('酷我解析失败');
}

async function parseNetease(id, quality) {
  const reqUrl = 'https://music.163.com/api/song/enhance/player/url?ids=[' + id + ']&br=320000';
  const res = await fetch(reqUrl, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://music.163.com/' } });
  const data = await res.json();
  if (data?.data?.[0]?.url) return data.data[0].url.replace('http://', 'https://');
  throw new Error('网易云解析失败');
}

async function parseMigu(copyrightId, quality) {
  const reqUrl = 'https://c.musicquery.migu.cn/v1.0/content/share_new.do?contentId=' + copyrightId + '&contenttype=1';
  const res = await fetch(reqUrl, { headers: { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)', 'channel': '0146951' } });
  const data = await res.json();
  if (data?.info?.url) return data.info.url;
  throw new Error('咪咕解析失败');
}
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> 文件生成成功！")

if __name__ == "__main__":
    build_all()
