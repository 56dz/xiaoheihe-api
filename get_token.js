// 抓取 xiaoheihe 的两个关键 cookie：x_xhh_tokenid（风控）与 user_pkey（登录态）。
//
// 两种模式：
//   1. 默认：拉一个全新的 headless Chrome（独立 profile），只能拿到匿名 cookie
//      + x_xhh_tokenid；user_pkey 为空。
//   2. 附着你自己的 Chrome：先用
//        chrome.exe --remote-debugging-port=9333 --user-data-dir=<你的 profile>
//      启动（已登录小黑盒），再跑
//        node get_token.js --attach 9333
//      这样 user_pkey 与 x_xhh_tokenid 都能从同一个 profile 里读出。
//
// 产物 cookie.json：{ cookie, token, pkey, heybox_id, ua }

const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const CHROME =
  process.env.CHROME_PATH ||
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const PORT = 9333;
const PROFILE = path.join(__dirname, '.chrome-profile');
const HOME = 'https://www.xiaoheihe.cn/app/bbs/home';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function getJSON(url) {
  const r = await fetch(url);
  return r.json();
}

class CDP {
  constructor(ws) {
    this.ws = ws;
    this.id = 0;
    this.pending = new Map();
    ws.addEventListener('message', (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        const { res, rej } = this.pending.get(msg.id);
        this.pending.delete(msg.id);
        msg.error ? rej(new Error(JSON.stringify(msg.error))) : res(msg.result);
      }
    });
  }
  send(method, params = {}, sessionId) {
    const id = ++this.id;
    return new Promise((res, rej) => {
      this.pending.set(id, { res, rej });
      this.ws.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
}

async function waitVersion(port, tries = 40) {
  for (let i = 0; i < tries; i++) {
    try {
      return await getJSON(`http://127.0.0.1:${port}/json/version`);
    } catch {
      await sleep(250);
    }
  }
  return null;
}

function pick(cookies, name) {
  const hit = cookies.find((c) => c.name === name);
  return hit ? hit.value : '';
}

function toCookieHeader(cookies) {
  return cookies
    .filter((c) => /xiaoheihe\.cn$/.test(c.domain.replace(/^\./, '')))
    .map((c) => `${c.name}=${c.value}`)
    .join('; ');
}

(async () => {
  const attachPort = process.argv[2] === '--attach' ? Number(process.argv[3] || PORT) : 0;
  let chrome = null;
  let port = attachPort;

  if (!attachPort) {
    chrome = spawn(
      CHROME,
      [
        '--headless=new',
        `--remote-debugging-port=${PORT}`,
        `--user-data-dir=${PROFILE}`,
        '--no-first-run',
        '--no-default-browser-check',
        '--disable-gpu',
        '--window-size=1280,900',
        'about:blank',
      ],
      { stdio: 'ignore', detached: false }
    );
    port = PORT;
  }

  const ver = await waitVersion(port);
  if (!ver) {
    console.error(`CDP 端口 ${port} 连不上`);
    if (chrome) chrome.kill();
    process.exit(1);
  }
  console.log('browser:', ver.Browser);

  const ws = new WebSocket(ver.webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r));
  const cdp = new CDP(ws);

  const { targetId } = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const { sessionId } = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Network.enable', {}, sessionId);
  await cdp.send('Page.navigate', { url: HOME }, sessionId);
  await sleep(7000);

  // Network.getAllCookies 能拿到 HttpOnly 的部分，document.cookie 拿不到
  const { cookies } = await cdp.send('Network.getAllCookies', {}, sessionId);
  const token = pick(cookies, 'x_xhh_tokenid');
  const pkey = pick(cookies, 'user_pkey');
  const heyboxId = pick(cookies, 'heybox_id');
  const cookie = toCookieHeader(cookies);

  console.log('x_xhh_tokenid:', token ? 'ok' : '(缺失)');
  console.log('user_pkey    :', pkey ? 'ok' : '(缺失，未登录或未附着已登录 Chrome)');

  const out = {
    cookie,
    token,
    pkey,
    heybox_id: heyboxId,
    ua: ver['User-Agent'],
  };
  fs.writeFileSync(path.join(__dirname, 'cookie.json'), JSON.stringify(out, null, 1), 'utf-8');
  console.log('已写入 cookie.json');

  ws.close();
  try {
    await cdp.send('Browser.close');
  } catch {}
  if (chrome) chrome.kill();
  process.exit(0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
