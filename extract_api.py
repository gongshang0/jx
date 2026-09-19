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
 * @description 实时解析音源 (防爬安全加固)
 * @version 1.0.0
 */

const { EVENT_NAMES, request, on, send } = globalThis.lx;
const SECRET = '""" + API_SECRET + """';

// 轻量级 MD5 签名方法
function md5(string) {
  function rotateLeft(lValue, iShiftBits) {
    return (lValue << iShiftBits) | (lValue >>> (32 - iShiftBits));
  }
  function addUnsigned(lX, lY) {
    var lX4, lY4, lX8, lY8, lResult;
    lX8 = (lX & 0x80000000); lY8 = (lY & 0x80000000);
    lX4 = (lX & 0x40000000); lY4 = (lY & 0x40000000);
    lResult = (lX & 0x3FFFFFFF) + (lY & 0x3FFFFFFF);
    if (lX4 & lY4) return (lResult ^ 0x80000000 ^ lX8 ^ lY8);
    if (lX4 | lY4) {
      if (lResult & 0x40000000) return (lResult ^ 0xC0000000 ^ lX8 ^ lY8);
      else return (lResult ^ 0x40000000 ^ lX8 ^ lY8);
    } else return (lResult ^ lX8 ^ lY8);
  }
  function F(x, y, z) { return (x & y) | ((~x) & z); }
  function G(x, y, z) { return (x & z) | (y & (~z)); }
  function H(x, y, z) { return (x ^ y ^ z); }
  function I(x, y, z) { return (y ^ (x | (~z))); }
  function FF(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(F(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }
  function GG(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(G(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }
  function HH(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(H(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }
  function II(a, b, c, d, x, s, ac) {
    a = addUnsigned(a, addUnsigned(addUnsigned(I(b, c, d), x), ac));
    return addUnsigned(rotateLeft(a, s), b);
  }
  function convertToWordArray(string) {
    var lWordCount;
    var lMessageLength = string.length;
    var lNumberOfWords_temp1 = lMessageLength + 8;
    var lNumberOfWords_temp2 = (lNumberOfWords_temp1 - (lNumberOfWords_temp1 % 64)) / 64;
    var lNumberOfWords = (lNumberOfWords_temp2 + 1) * 16;
    var lWordArray = Array(lNumberOfWords - 1);
    var lBytePosition = 0;
    var lByteCount = 0;
    while (lByteCount < lMessageLength) {
      lWordCount = (lByteCount - (lByteCount % 4)) / 4;
      lBytePosition = (lByteCount % 4) * 8;
      lWordArray[lWordCount] = (lWordArray[lWordCount] | (string.charCodeAt(lByteCount) << lBytePosition));
      lByteCount++;
    }
    lWordCount = (lByteCount - (lByteCount % 4)) / 4;
    lBytePosition = (lByteCount % 4) * 8;
    lWordArray[lWordCount] = lWordArray[lWordCount] | (0x80 << lBytePosition);
    lWordArray[lNumberOfWords - 2] = lMessageLength << 3;
    lWordArray[lNumberOfWords - 1] = lMessageLength >>> 29;
    return lWordArray;
  }
  function wordToHex(lValue) {
    var WordToHexValue = "", WordToHexValue_temp = "", lByte, lCount;
    for (lCount = 0; lCount <= 3; lCount++) {
      lByte = (lValue >>> (lCount * 8)) & 255;
      WordToHexValue_temp = "0" + lByte.toString(16);
      WordToHexValue = WordToHexValue + WordToHexValue_temp.substr(WordToHexValue_temp.length - 2, 2);
    }
    return WordToHexValue;
  }
  var x = Array();
  var k, AA, BB, CC, DD, a, b, c, d;
  var S11=7, S12=12, S13=17, S14=22;
  var S21=5, S22=9, S23=14, S24=20;
  var S31=4, S32=11, S33=16, S34=23;
  var S41=6, S42=10, S43=15, S44=21;
  x = convertToWordArray(string);
  a = 0x67452301; b = 0xEFCDAB89; c = 0x98BADCFE; d = 0x10325476;
  for (k = 0; k < x.length; k += 16) {
    AA = a; BB = b; CC = c; DD = d;
    a = FF(a, b, c, d, x[k+0], S11, 0xD76AA478); d = FF(d, a, b, c, x[k+1], S12, 0xE8C7B756); c = FF(c, d, a, b, x[k+2], S13, 0x242070DB); b = FF(b, c, d, a, x[k+3], S14, 0xC1BDCEEE);
    a = FF(a, b, c, d, x[k+4], S11, 0xF57C0FAF); d = FF(d, a, b, c, x[k+5], S12, 0x4787C62A); c = FF(c, d, a, b, x[k+6], S13, 0xA8304613); b = FF(b, c, d, a, x[k+7], S14, 0xFD469501);
    a = FF(a, b, c, d, x[k+8], S11, 0x698098D8); d = FF(d, a, b, c, x[k+9], S12, 0x8B44F7AF); c = FF(c, d, a, b, x[k+10], S13, 0xFFFF5BB1); b = FF(b, c, d, a, x[k+11], S14, 0x895CD7BE);
    a = FF(a, b, c, d, x[k+12], S11, 0x6B901122); d = FF(d, a, b, c, x[k+13], S12, 0xFD987193); c = FF(c, d, a, b, x[k+14], S13, 0xA679438E); b = FF(b, c, d, a, x[k+15], S14, 0x49B40821);
    a = GG(a, b, c, d, x[k+1], S21, 0xF61E2562); d = GG(d, a, b, c, x[k+6], S22, 0xC040B340); c = GG(c, d, a, b, x[k+11], S23, 0x265E5A51); b = GG(b, c, d, a, x[k+0], S24, 0xE9B6C7AA);
    a = GG(a, b, c, d, x[k+5], S21, 0xD62F105D); d = GG(d, a, b, c, x[k+10], S22, 0x2441453); c = GG(c, d, a, b, x[k+15], S23, 0xD8A1E681); b = GG(b, c, d, a, x[k+4], S24, 0xE7D3FBC8);
    a = GG(a, b, c, d, x[k+9], S21, 0x21E1CDE6); d = GG(d, a, b, c, x[k+14], S22, 0xC33707D6); c = GG(c, d, a, b, x[k+3], S23, 0xF4D50D87); b = GG(b, c, d, a, x[k+8], S24, 0x455A14ED);
    a = GG(a, b, c, d, x[k+13], S21, 0xA9E3E905); d = GG(d, a, b, c, x[k+2], S22, 0xFCEFA3F8); c = GG(c, d, a, b, x[k+7], S23, 0x676F02D9); b = GG(b, c, d, a, x[k+12], S24, 0x8D2A4C8A);
    a = HH(a, b, c, d, x[k+5], S31, 0xFFFA3942); d = HH(d, a, b, c, x[k+8], S32, 0x8771F681); c = HH(c, d, a, b, x[k+11], S33, 0x6D9D6122); b = HH(b, c, d, a, x[k+14], S34, 0xFDE5380C);
    a = HH(a, b, c, d, x[k+1], S31, 0xA4BEEA44); d = HH(d, a, b, c, x[k+4], S32, 0x4BDECFA9); c = HH(c, d, a, b, x[k+7], S33, 0xF6BB4B60); b = HH(b, c, d, a, x[k+10], S34, 0xBEBFBC70);
    a = HH(a, b, c, d, x[k+13], S31, 0x289B7EC6); d = HH(d, a, b, c, x[k+0], S32, 0xEAA127FA); c = HH(c, d, a, b, x[k+3], S33, 0xD4EF3085); b = HH(b, c, d, a, x[k+6], S34, 0x04881D05);
    a = HH(a, b, c, d, x[k+9], S31, 0xD9D4D039); d = HH(d, a, b, c, x[k+12], S32, 0xE6DB99E5); c = HH(c, d, a, b, x[k+15], S33, 0x1FA27CF8); b = HH(b, c, d, a, x[k+2], S34, 0xC4AC5665);
    a = II(a, b, c, d, x[k+0], S41, 0xF4292244); d = II(d, a, b, c, x[k+3], S42, 0x432AFF97); c = II(c, d, a, b, x[k+10], S43, 0xAB9423A7); b = II(b, c, d, a, x[k+1], S44, 0xFC93A039);
    a = II(a, b, c, d, x[k+8], S41, 0x655B59C3); d = II(d, a, b, c, x[k+15], S42, 0x8F0CCC92); c = II(c, d, a, b, x[k+6], S43, 0xFFEFF47D); b = II(b, c, d, a, x[k+13], S44, 0x85845DD1);
    a = II(a, b, c, d, x[k+4], S41, 0x6FA87E4F); d = II(d, a, b, c, x[k+11], S42, 0xFE2CE6E0); c = II(c, d, a, b, x[k+2], S43, 0xA3014314); b = II(b, c, d, a, x[k+9], S44, 0x4E0811A1);
    a = addUnsigned(a, AA); b = addUnsigned(b, BB); c = addUnsigned(c, CC); d = addUnsigned(d, DD);
  }
  return (wordToHex(a) + wordToHex(b) + wordToHex(c) + wordToHex(d)).toLowerCase();
}

// 客户端加载时直接发起请求响应
on(EVENT_NAMES.request, async ({ action, source, musicInfo, quality }) => {
  if (action === 'musicUrl') {
    const songId = musicInfo.songmid || musicInfo.id;
    const t = Math.floor(Date.now() / 1000);
    // 签名: md5(source + id + quality + time + SECRET)
    const sign = md5(source + songId + quality + t + SECRET);

    const apiUrl = WORKER_URL + '/?source=' + source + '&id=' + songId + '&quality=' + quality + '&t=' + t + '&sign=' + sign;

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

    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': '*',
      'Content-Type': 'application/javascript; charset=utf-8'
    };

    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    if (url.pathname === '/lx-source.js') {
      return new Response(CLIENT_SCRIPT, {
        headers: { ...corsHeaders, 'Content-Type': 'application/javascript; charset=utf-8' }
      });
    }

    const jsonHeaders = { ...corsHeaders, 'Content-Type': 'application/json; charset=utf-8' };

    const source = url.searchParams.get('source');
    const songmid = url.searchParams.get('id');
    const quality = url.searchParams.get('quality') || '128k';
    const t = parseInt(url.searchParams.get('t') || '0', 10);
    const sign = url.searchParams.get('sign');

    if (!source || !songmid || !t || !sign) {
      return new Response(JSON.stringify({ code: 401, msg: 'Unauthorized Request' }), { status: 401, headers: jsonHeaders });
    }

    const now = Math.floor(Date.now() / 1000);
    if (Math.abs(now - t) > 30) {
      return new Response(JSON.stringify({ code: 403, msg: 'Link expired' }), { status: 403, headers: jsonHeaders });
    }

    const expectedSign = await md5WebCrypto(source + songmid + quality + t + API_SECRET);
    if (sign !== expectedSign) {
      return new Response(JSON.stringify({ code: 403, msg: 'Invalid Signature' }), { status: 403, headers: jsonHeaders });
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

async function md5WebCrypto(str) {
  const encoder = new TextEncoder();
  const data = encoder.encode(str);
  const hashBuffer = await crypto.subtle.digest('MD5', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

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
