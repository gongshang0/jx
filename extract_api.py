import os

def build_all():
    print(">>> 正在生成配置与部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"
    API_SECRET = "MusicDL_SecretKey_2026_Secure"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';
const API_SECRET = '""" + API_SECRET + """';

// 极致精简的客户端脚本：绝不出错，百分百初始化成功并透传解析
const CLIENT_SCRIPT = `/**
 * @name MusicDL 自动化源
 * @description 全平台解析音源 (稳定修复版)
 * @version 1.2.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;

// 1. 发送初始化成功通知
send(EVENT_NAMES.inited, {
  status: true,
  openDevTools: false,
  sources: {
    kw: { name: '酷我音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    kg: { name: '酷狗音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    tx: { name: 'QQ音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    wy: { name: '网易云音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    mg: { name: '咪咕音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] }
  }
});

// 2. 监听请求并透传给后端 Worker
on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    const songId = musicInfo.songmid || musicInfo.hash || musicInfo.id || musicInfo.copyrightId;
    const apiUrl = WORKER_URL + '/parse?source=' + source + '&id=' + encodeURIComponent(songId) + '&quality=' + quality + '&secret=' + '""" + API_SECRET + """';

    try {
      const res = await request(apiUrl, { method: 'GET', timeout: 10000 });
      const body = typeof res.body === 'string' ? JSON.parse(res.body) : res.body;
      if (body && body.code === 0 && body.url) {
        return body.url;
      }
      throw new Error(body.msg || '无法获取播放链接');
    } catch (err) {
      throw new Error('解析失败: ' + err.message);
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
      'Cache-Control': 'no-cache, no-store, must-revalidate'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // 提供 JS 脚本服务
    if (url.pathname === '/lx-source.js') {
      return new Response(CLIENT_SCRIPT, {
        headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' }
      });
    }

    // 解析音源接口
    if (url.pathname === '/parse') {
      const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };

      const source = url.searchParams.get('source');
      const songmid = url.searchParams.get('id');
      const quality = url.searchParams.get('quality') || '128k';
      const secret = url.searchParams.get('secret');

      if (secret !== API_SECRET) {
        return new Response(JSON.stringify({ code: 403, msg: '密钥不匹配，拒绝访问' }), { status: 403, headers: jsonHeaders });
      }

      if (!source || !songmid) {
        return new Response(JSON.stringify({ code: 400, msg: '缺少必备参数' }), { status: 400, headers: jsonHeaders });
      }

      try {
        const musicUrl = await getRealPlayUrl(source, songmid, quality);
        return new Response(JSON.stringify({ code: 0, url: musicUrl }), { headers: jsonHeaders });
      } catch (err) {
        return new Response(JSON.stringify({ code: 500, msg: err.message }), { status: 500, headers: jsonHeaders });
      }
    }

    return new Response('MusicDL Worker Active', { status: 200, headers: corsHeaders });
  }
};

// 后端多重备用链接智能解析引擎
async function getRealPlayUrl(source, id, quality) {
  // 渠道 1：免费公用解析 API
  try {
    const res = await fetch(`https://api.vkey.lgqy.hn.cn/api/music?source=${source}&id=${id}&quality=${quality}`, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    const data = await res.json();
    if (data && data.url && data.url.startsWith('http')) {
      return data.url;
    }
  } catch (e) {}

  // 渠道 2：咪咕直连接口
  if (source === 'mg') {
    try {
      const res = await fetch(`https://c.musicquery.migu.cn/v1.0/content/share_new.do?contentId=${id}&contenttype=1`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)', 'channel': '0146951' }
      });
      const data = await res.json();
      if (data?.info?.url) return data.info.url;
    } catch (e) {}
  }

  // 渠道 3：酷我直连接口
  if (source === 'kw') {
    try {
      const res = await fetch(`https://antiserver.kuwo.cn/anti.s?type=convert_url&rid=${id}&format=mp3&response=url`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
      });
      const text = await res.text();
      if (text && text.startsWith('http')) return text;
    } catch (e) {}
  }

  // 渠道 4：网易云直连接口
  if (source === 'wy') {
    try {
      const res = await fetch(`https://music.163.com/api/song/enhance/player/url?ids=[${id}]&br=320000`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Referer': 'https://music.163.com/' }
      });
      const data = await res.json();
      if (data?.data?.[0]?.url) return data.data[0].url.replace('http://', 'https://');
    } catch (e) {}
  }

  throw new Error('所有线路解析失败，该歌曲可能受版权保护');
}
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> 文件生成成功！")

if __name__ == "__main__":
    build_all()
