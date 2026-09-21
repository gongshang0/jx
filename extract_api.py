import os

def build_all():
    print(">>> 正在生成彻底稳定的高可用 Worker 部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"
    API_SECRET = "MusicDL_SecretKey_2026_Secure"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';
const API_SECRET = '""" + API_SECRET + """';

const CLIENT_SCRIPT = `/**
 * @name MusicDL 极速高可用源
 * @description 彻底解决 Cloudflare IP 限制，多节点毫秒级抢跑
 * @version 3.0.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;

send(EVENT_NAMES.inited, {
  status: true,
  openDevTools: false,
  sources: {
    kw: { name: '酷我音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    kg: { name: '酷狗音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    wy: { name: '网易云音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    mg: { name: '咪咕音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] },
    tx: { name: 'QQ音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k', 'flac'] }
  }
});

on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    let songId = musicInfo.songmid || musicInfo.id;
    if (source === 'kg') {
      songId = musicInfo.hash || musicInfo.sqHash || musicInfo.hqHash || musicInfo.songmid || musicInfo.id;
    } else if (source === 'tx') {
      songId = musicInfo.songmid || musicInfo.strMediaMid || musicInfo.id;
    }

    const apiUrl = WORKER_URL + '/parse?source=' + source + '&id=' + encodeURIComponent(songId) + '&quality=' + (quality || '128k') + '&secret=' + API_SECRET;

    try {
      const res = await request(apiUrl, { method: 'GET', timeout: 12000 });
      const body = typeof res.body === 'string' ? JSON.parse(res.body) : res.body;
      if (body && body.code === 0 && body.url) {
        return body.url;
      }
      throw new Error(body.msg || '未获取到有效播放地址');
    } catch (err) {
      throw new Error(err.message || '网络请求超时');
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
      const quality = url.searchParams.get('quality') || '128k';
      const secret = url.searchParams.get('secret');

      if (secret !== API_SECRET) {
        return new Response(JSON.stringify({ code: 403, msg: '密钥不匹配' }), { status: 403, headers: jsonHeaders });
      }

      if (!source || !songmid) {
        return new Response(JSON.stringify({ code: 400, msg: '参数不完整' }), { status: 400, headers: jsonHeaders });
      }

      try {
        const musicUrl = await fetchClusterUrl(source, songmid, quality);
        if (musicUrl) {
          return new Response(JSON.stringify({ code: 0, url: musicUrl }), { headers: jsonHeaders });
        }
        return new Response(JSON.stringify({ code: 404, msg: '全网解析节点均未命中有效音源' }), { status: 200, headers: jsonHeaders });
      } catch (err) {
        return new Response(JSON.stringify({ code: 500, msg: '解析服务异常: ' + err.message }), { status: 200, headers: jsonHeaders });
      }
    }

    return new Response('MusicDL High-Availability Cluster Online', { status: 200, headers: corsHeaders });
  }
};

// 核心并发解析集群
async function fetchClusterUrl(source, songid, quality) {
  // 定义全网稳定解析节点池
  const nodes = [
    `https://api.ikunshare.com/api/music?source=${source}&id=${songid}&quality=${quality}`,
    `https://lxmusicapi.onrender.com/url/${source}/${songid}/${quality}`,
    `https://lx.xms.ink/api/music?source=${source}&id=${songid}&quality=${quality}`
  ];

  // 构造并发请求任务
  const fetchTasks = nodes.map(nodeUrl => {
    return new Promise((resolve, reject) => {
      fetch(nodeUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
      })
      .then(res => res.json())
      .then(data => {
        const playUrl = data?.url || data?.data?.url || (typeof data?.data === 'string' && data.data.startsWith('http') ? data.data : '');
        if (playUrl && playUrl.startsWith('http')) {
          resolve(playUrl);
        } else {
          reject(new Error('Invalid URL'));
        }
      })
      .catch(err => reject(err));
    });
  });

  // 使用 Promise.any 算法：任意一个节点率先返回成功结果即可，彻底防止单点失效
  try {
    const fastestUrl = await Promise.any(fetchTasks);
    return fastestUrl;
  } catch (err) {
    return '';
  }
}
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> worker.js 生成成功！")

if __name__ == "__main__":
    build_all()
