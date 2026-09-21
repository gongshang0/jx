import os

def build_all():
    print(">>> 正在生成对接 Go Music DL 后端的 Worker 部署文件...")

    CUSTOM_API_DOMAIN = "https://lx.gongshangss.dpdns.org"
    # 使用该 Go 项目的 API 节点
    GO_API_BASE = "https://music.zkkp.nyc.mn"

    worker_code = """
const WORKER_URL = '""" + CUSTOM_API_DOMAIN + """';
const GO_API_BASE = '""" + GO_API_BASE + """';

const CLIENT_SCRIPT = `/**
 * @name MusicDL (Go-Backend)
 * @description 基于 Go-Music-DL 节点的洛雪自定义源
 * @version 5.0.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;

send(EVENT_NAMES.inited, {
  status: true,
  openDevTools: false,
  sources: {
    kw: { name: '酷我音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    kg: { name: '酷狗音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    wy: { name: '网易云音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    mg: { name: '咪咕音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] },
    tx: { name: '企鹅音乐', type: 'music', actions: ['musicUrl'], qualitys: ['128k', '320k'] }
  }
});

const sourceMap = {
  wy: 'netease',
  tx: 'qq',
  kg: 'kugou',
  kw: 'kuwo',
  mg: 'migu'
};

on(EVENT_NAMES.request, ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    let songId = musicInfo.songmid || musicInfo.id;
    if (source === 'kg') {
      songId = musicInfo.hash || musicInfo.sqHash || musicInfo.hqHash || musicInfo.songmid || musicInfo.id;
    } else if (source === 'tx') {
      songId = musicInfo.songmid || musicInfo.strMediaMid || musicInfo.id;
    }

    const apiUrl = WORKER_URL + '/parse?source=' + source + '&id=' + encodeURIComponent(songId) + '&quality=' + (quality || '128k');

    return request(apiUrl, { method: 'GET', timeout: 12000 }).then(res => {
      const body = typeof res.body === 'string' ? JSON.parse(res.body) : res.body;
      if (body && body.code === 0 && body.url) {
        return body.url;
      }
      return Promise.reject(new Error(body.msg || '无法获取音频链接'));
    });
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

      if (!source || !songmid) {
        return new Response(JSON.stringify({ code: 400, msg: '参数不完整' }), { status: 200, headers: jsonHeaders });
      }

      // 映射洛雪平台名称到 Go-Music-DL 平台的标识
      const platformMap = { wy: 'netease', tx: 'qq', kg: 'kugou', kw: 'kuwo', mg: 'migu' };
      const goSource = platformMap[source] || source;

      try {
        // 请求 Go 后端的 url 获取接口
        const targetUrl = `${GO_API_BASE}/music/url?source=${goSource}&id=${encodeURIComponent(songmid)}`;
        const res = await fetch(targetUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': GO_API_BASE
          }
        });
        
        const data = await res.json();
        const playUrl = data?.url || data?.data?.url || (typeof data?.data === 'string' && data.data.startsWith('http') ? data.data : '');

        if (playUrl && playUrl.startsWith('http')) {
          return new Response(JSON.stringify({ code: 0, url: playUrl }), { headers: jsonHeaders });
        }

        return new Response(JSON.stringify({ code: 404, msg: 'Go后端未解析到播放链接' }), { status: 200, headers: jsonHeaders });
      } catch (err) {
        return new Response(JSON.stringify({ code: 500, msg: '请求Go后端异常: ' + err.message }), { status: 200, headers: jsonHeaders });
      }
    }

    return new Response('MusicDL Go-Gateway Active', { status: 200, headers: corsHeaders });
  }
};
"""

    with open("worker.js", "w", encoding="utf-8") as f:
        f.write(worker_code)

    print(">>> worker.js 更新完成！")

if __name__ == "__main__":
    build_all()
