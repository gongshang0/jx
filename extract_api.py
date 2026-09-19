import os

def build_all():
    print(">>> 正在生成配置与部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"
    API_SECRET = "MusicDL_SecretKey_2026_Secure"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';
const API_SECRET = '""" + API_SECRET + """';

const CLIENT_SCRIPT = `/**
 * @name MusicDL 自动化源
 * @description 全平台解析音源 (酷狗/周杰伦算法修复版)
 * @version 1.3.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;

// 1. 初始化通知
send(EVENT_NAMES.inited, {
  status: true,
  openDevTools: false,
  sources: {
    kw: { name: '酷我音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    kg: { name: '酷狗音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    tx: { name: 'QQ音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    wy: { name: '网易云音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    mg: { name: '咪咕音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] }
  }
});

// 2. 请求转发机制（对酷狗 hash 做特异性处理）
on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    let songId = musicInfo.songmid || musicInfo.id;

    // 针对酷狗源特殊处理：酷狗的核心核心是 hash
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

    if (url.pathname === '/lx-source.js') {
      return new Response(CLIENT_SCRIPT, {
        headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' }
      });
    }

    if (url.pathname === '/parse') {
      const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };

      const source = url.searchParams.get('source');
      const songmid = url.searchParams.get('id');
      const quality = url.searchParams.get('quality') || '128k';
      const secret = url.searchParams.get('secret');

      if (secret !== API_SECRET) {
        return new Response(JSON.stringify({ code: 403, msg: '密钥不匹配' }), { status: 403, headers: jsonHeaders });
      }

      if (!source || !songmid) {
        return new Response(JSON.stringify({ code: 400, msg: '缺少参数' }), { status: 400, headers: jsonHeaders });
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

async function getRealPlayUrl(source, id, quality) {
  // 渠道 1：专治周杰伦及无损版权的聚合接口
  try {
    const res = await fetch(`https://api.ikunshare.com/api/music?source=${source}&id=${id}&quality=${quality}`, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    const data = await res.json();
    if (data && data.url && data.url.startsWith('http')) return data.url;
    if (data && data.data && typeof data.data === 'string' && data.data.startsWith('http')) return data.data;
  } catch (e) {}

  // 渠道 2：全网兼容接口
  try {
    const res = await fetch(`https://api.vkey.lgqy.hn.cn/api/music?source=${source}&id=${id}&quality=${quality}`, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    const data = await res.json();
    if (data && data.url && data.url.startsWith('http')) return data.url;
  } catch (e) {}

  // 渠道 3：酷狗专项 Hash 直连解析
  if (source === 'kg') {
    try {
      const res = await fetch(`https://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo&hash=${id}`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)' }
      });
      const data = await res.json();
      if (data && data.url) return data.url;
    } catch (e) {}
  }

  // 渠道 4：酷我直连
  if (source === 'kw') {
    try {
      const res = await fetch(`https://antiserver.kuwo.cn/anti.s?type=convert_url&rid=${id}&format=mp3&response=url`, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
      });
      const text = await res.text();
      if (text && text.startsWith('http')) return text;
    } catch (e) {}
  }

  throw new Error('该歌曲所有解析接口均未返回有效地址');
}
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> 文件生成成功！")

if __name__ == "__main__":
    build_all()
